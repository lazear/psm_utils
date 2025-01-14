from __future__ import annotations

from pyteomics import mass, proforma
import numpy as np

from psm_utils.exceptions import PSMUtilsException


class Peptidoform:
    """
    Peptide sequence, modifications and charge state represented in ProForma notation.
    """

    def __init__(self, proforma_sequence: str) -> None:
        """
        Peptide sequence, modifications and charge state represented in ProForma notation.

        Parameters
        ----------
        proforma_sequence : str
            Peptidoform sequence in ProForma v2 notation.

        Examples
        --------
        >>> peptidoform = Peptidoform("ACDM[Oxidation]EK")
        >>> peptidoform.theoretical_mass
        711.2567622919099

        Attributes
        ----------
        parsed_sequence : list
            List of tuples with residue and modifications for each location.
        properties : dict[str, Any]
            Dict with sequence-wide properties.

        """
        self.parsed_sequence, self.properties = proforma.parse(proforma_sequence)

        if self.properties["isotopes"]:
            raise NotImplementedError(
                "Peptidoforms with isotopes are currently not supported."
            )

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}('{self.proforma}')"

    def __str__(self) -> str:
        return self.proforma

    def __hash__(self) -> int:
        return hash(self.proforma)

    def __eq__(self, __o: Peptidoform) -> bool:
        try:
            return self.proforma == __o.proforma
        except AttributeError:
            raise NotImplemented("Object is not a Peptidoform")

    @property
    def proforma(self) -> str:
        """
        Peptidoform sequence in ProForma v2 notation.

        Examples
        --------
        >>> Peptidoform("AC[U:4]DEK/2").proforma
        'AC[UNIMOD:4]DEK/2'

        """
        return proforma.to_proforma(self.parsed_sequence, **self.properties)

    @property
    def sequence(self) -> str:
        """
        Stripped peptide sequence (modifications removed).

        Examples
        --------
        >>> Peptidoform("AC[U:4]DEK/2").sequence
        'ACDEK'

        """
        return "".join(pos[0] for pos in self.parsed_sequence)

    @property
    def precursor_charge(self) -> int | None:
        """
        Returns the charge state as integer or :py:const:`None` if no charge assigned.

        Examples
        --------
        >>> Peptidoform("ACDEK/2").precursor_charge
        2

        >>> Peptidoform("ACDEK").precursor_charge
        None

        """
        try:
            return self.properties["charge_state"].charge
        except (AttributeError, KeyError):
            return None

    @property
    def is_modified(self) -> bool:
        """
        Whether or not the peptidoform carries any modification of any type.

        Includes N- and C-terminal, fixed, sequential, labile, and unlocalized
        modifications.

        """
        mod_properties = [
            "n_term",
            "c_term",
            "unlocalized_modifications",
            "labile_modifications",
            "fixed_modifications",
        ]
        has_sequential = any(mods for _, mods in self.parsed_sequence)
        has_other = any([self.properties[prop] for prop in mod_properties])
        return has_sequential or has_other

    @property
    def sequential_composition(self) -> list[mass.Composition]:
        """
        Atomic compositions of both termini and each residue, including modifications.

        Includes N- and C-terminal, fixed, and sequential modifications. Does not
        include labile or unlocalized modifications.

        Examples
        --------
        >>> Peptidoform("ACDEK/2").sequential_composition
        [Composition({'H': 1}),
        Composition({'H': 5, 'C': 3, 'O': 1, 'N': 1}),
        Composition({'H': 5, 'C': 3, 'S': 1, 'O': 1, 'N': 1}),
        Composition({'H': 5, 'C': 4, 'O': 3, 'N': 1}),
        Composition({'H': 7, 'C': 5, 'O': 3, 'N': 1}),
        Composition({'H': 12, 'C': 6, 'N': 2, 'O': 1}),
        Composition({'H': 1, 'O': 1})]

        """
        # Get compositions for fixed modifications by amino acid
        fixed_rules = {}
        for rule in self.properties["fixed_modifications"]:
            for aa in rule.targets:
                fixed_rules[aa] = rule.modification_tag.composition

        comp_list = []

        # N-terminus
        n_term = mass.Composition({"H": 1})
        if self.properties["n_term"]:
            for tag in self.properties["n_term"]:
                try:
                    n_term += tag.composition
                except (AttributeError, KeyError):
                    raise ModificationException(
                        f"Cannot resolve composition for modification {tag.value}."
                    )
        comp_list.append(n_term)

        # Sequence
        for aa, tags in self.parsed_sequence:
            # Amino acid
            try:
                position_comp = mass.std_aa_comp[aa].copy()
            except (AttributeError, KeyError):
                raise AmbiguousResidueException(
                    f"Cannot resolve composition for amino acid {aa}."
                )
            # Fixed modifications
            if aa in fixed_rules:
                position_comp += fixed_rules[aa]
            # Localized modifications
            if tags:
                for tag in tags:
                    try:
                        position_comp += tag.composition
                    except (AttributeError, KeyError):
                        raise ModificationException(
                            "Cannot resolve composition for modification "
                            f"{tag.value}."
                        )
            comp_list.append(position_comp)

        # C-terminus
        c_term = mass.Composition({"H": 1, "O": 1})
        if self.properties["c_term"]:
            for tag in self.properties["c_term"]:
                try:
                    c_term += tag.composition
                except (AttributeError, KeyError):
                    raise ModificationException(
                        f"Cannot resolve composition for modification {tag.value}."
                    )
        comp_list.append(c_term)

        return comp_list

    @property
    def composition(self) -> mass.Composition:
        """
        Atomic composition of the full peptidoform.

        Includes all modifications, also labile and unlocalized.

        Examples
        --------
        >>> Peptidoform("ACDEK/2").composition
        Composition({'H': 36, 'C': 21, 'O': 10, 'N': 6, 'S': 1})

        """
        comp = mass.Composition()
        for position_comp in self.sequential_composition:
            comp += position_comp
        for tag in self.properties["labile_modifications"]:
            try:
                comp += tag.composition
            except (AttributeError, KeyError):
                raise ModificationException(
                    f"Cannot resolve composition for modification {tag.value}."
                )
        for tag in self.properties["unlocalized_modifications"]:
            try:
                comp += tag.composition
            except (AttributeError, KeyError):
                raise ModificationException(
                    f"Cannot resolve composition for modification {tag.value}."
                )
        return comp

    @property
    def sequential_theoretical_mass(self) -> float:
        """
        Monoisotopic mass of both termini and each (modified) residue.

        Includes N- and C-terminal, fixed, and sequential modifications. Does not
        include labile or unlocalized modifications.

        Examples
        --------
        >>> Peptidoform("ACDEK/2").sequential_theoretical_mass
        [1.00782503207,
        71.03711378471,
        103.00918478471,
        115.02694302383001,
        129.04259308796998,
        128.09496301399997,
        17.002739651629998]

        """
        fixed_rules = {}
        for rule in self.properties["fixed_modifications"]:
            for aa in rule.targets:
                fixed_rules[aa] = rule.modification_tag.mass

        mass_list = []

        # N-terminus
        n_term = mass.Composition({"H": 1}).mass()
        if self.properties["n_term"]:
            for tag in self.properties["n_term"]:
                try:
                    n_term += tag.mass
                except (AttributeError, KeyError):
                    raise ModificationException(
                        f"Cannot resolve mass for modification {tag.value}."
                    )
        mass_list.append(n_term)

        # Sequence
        for aa, tags in self.parsed_sequence:
            # Amino acid
            try:
                position_mass = mass.std_aa_mass[aa]
            except (AttributeError, KeyError):
                raise AmbiguousResidueException(
                    f"Cannot resolve mass for amino acid {aa}."
                )
            # Fixed modifications
            if aa in fixed_rules:
                position_mass += fixed_rules[aa]
            # Localized modifications
            if tags:
                for tag in tags:
                    try:
                        position_mass += tag.mass
                    except (AttributeError, KeyError):
                        raise ModificationException(
                            "Cannot resolve mass for modification " f"{tag.value}."
                        )
            mass_list.append(position_mass)

        # C-terminus
        c_term = mass.Composition({"H": 1, "O": 1}).mass()
        if self.properties["c_term"]:
            for tag in self.properties["c_term"]:
                try:
                    c_term += tag.mass
                except (AttributeError, KeyError):
                    raise ModificationException(
                        f"Cannot resolve mass for modification {tag.value}."
                    )
        mass_list.append(c_term)

        return mass_list

    @property
    def theoretical_mass(self) -> float:
        """Monoisotopic mass of the full uncharged peptidoform.

        Includes all modifications, also labile and unlocalized.

        Examples
        --------
        >>> Peptidoform("ACDEK/2").theoretical_mass
        564.22136237892

        """
        mass = sum(self.sequential_theoretical_mass)
        for tag in self.properties["labile_modifications"]:
            try:
                mass += tag.mass
            except (AttributeError, KeyError):
                raise ModificationException(
                    f"Cannot resolve mass for modification {tag.value}."
                )
        for tag in self.properties["unlocalized_modifications"]:
            try:
                mass += tag.mass
            except (AttributeError, KeyError):
                raise ModificationException(
                    f"Cannot resolve mass for modification {tag.value}."
                )
        return mass

    @property
    def theoretical_mz(self) -> float | None:
        """
        Monoisotopic mass-to-charge ratio of the full peptidoform.

        Includes all modifications, also labile and unlocalized.

        Examples
        --------
        >>> Peptidoform("ACDEK/2").theoretical_mz
        283.11850622153

        >>> Peptidoform("AC[+57.021464]DEK/2").theoretical_mz
        311.62923822153

        """
        if self.precursor_charge:
            return (
                self.theoretical_mass
                + (mass.nist_mass["H"][1][0] * self.precursor_charge)
            ) / self.precursor_charge
        else:
            return None

    def rename_modifications(self, mapping: dict[str, str]) -> None:
        """
        Apply mapping to rename modification tags.

        Parameters
        ----------
        mapping : dict[str, str]
            Mapping of ``old label`` → ``new label`` for each modification that
            requires renaming. Modification labels that are not in the mapping will not
            be renamed.

        See also
        --------
        psm_utils.psm_list.PSMList.rename_modifications

        Examples
        --------
        >>> peptidoform = Peptidoform('[ac]-PEPTC[cmm]IDEK')
        >>> peptidoform.rename_modifications({
        ...     "ac": "Acetyl",
        ...     "cmm": "Carbamidomethyl"
        ... })
        >>> peptidoform.proforma
        '[Acetyl]-PEPTC[Carbamidomethyl]IDEK'

        """

        def _rename_modification_list(mods):
            new_mods = []
            for mod in mods:
                try:
                    if isinstance(mod, proforma.MassModification):
                        mod_value = _format_number_as_string(mod.value)
                    else:
                        mod_value = mod.value
                    if mod_value in mapping:
                        new_mods.append(proforma.process_tag_tokens(mapping[mod_value]))
                    else:
                        new_mods.append(mod)
                except AttributeError:
                    if isinstance(mod, proforma.ModificationRule):
                        if mod.modification_tag.value in mapping:
                            mod.modification_tag = proforma.process_tag_tokens(
                                mapping[mod.modification_tag.value]
                            )
                        new_mods.append(mod)
                    else:
                        mod.value  # re-raise AttributeError
            return new_mods

        # Sequential modifications
        for i, (aa, mods) in enumerate(self.parsed_sequence):
            if mods:
                new_mods = _rename_modification_list(mods)
                self.parsed_sequence[i] = (aa, new_mods)

        # Non-sequence modifications
        for mod_type in [
            "n_term",
            "c_term",
            "unlocalized_modifications",
            "labile_modifications",
            "fixed_modifications",
        ]:
            if self.properties[mod_type]:
                self.properties[mod_type] = _rename_modification_list(
                    self.properties[mod_type]
                )

    def add_fixed_modifications(
        self, modification_rules: list[tuple[str, list[str]]] | dict[str, list[str]]
    ):
        """
        Add fixed modifications to peptidoform.

        Add modification rules for fixed modifications to peptidoform. These will be
        added in the "fixed modifications" notation, at the front of the ProForma
        sequence.

        See also
        --------
        psm_utils.peptidoform.Peptidoform.add_fixed_modifications

        Examples
        --------
        >>> peptidoform = Peptidoform("ATPEILTCNSIGCLK")
        >>> peptidoform.add_fixed_modifications([("Carbamidomethyl", ["C"])])
        >>> peptidoform.proforma
        '<[Carbamidomethyl]@C>ATPEILTCNSIGCLK'

        """
        if isinstance(modification_rules, dict):
            modification_rules = modification_rules.items()
        modification_rules = [
            proforma.ModificationRule(proforma.process_tag_tokens(mod), targets)
            for mod, targets in modification_rules
        ]
        if self.properties["fixed_modifications"]:
            self.properties["fixed_modifications"].extend(modification_rules)
        else:
            self.properties["fixed_modifications"] = modification_rules

    def apply_fixed_modifications(self):
        """
        Apply ProForma fixed modifications as sequential modifications.

        Applies all modifications that are encoded as fixed in the ProForma notation
        (once at the beginning of the sequence) as modifications throughout the
        sequence at each affected amino acid residue.

        See also
        --------
        psm_utils.peptidoform.Peptidoform.apply_fixed_modifications

        Examples
        --------
        >>> peptidoform = Peptidoform('<[Carbamidomethyl]@C>ATPEILTCNSIGCLK')
        >>> peptidoform.apply_fixed_modifications()
        >>> peptidoform.proforma
        'ATPEILTC[Carbamidomethyl]NSIGC[Carbamidomethyl]LK'

        """
        if self.properties["fixed_modifications"]:
            # Setup target_aa -> modification_list dictionary
            rule_dict = {}
            for rule in self.properties["fixed_modifications"]:
                for target_aa in rule.targets:
                    try:
                        rule_dict[target_aa].append(rule.modification_tag)
                    except KeyError:
                        rule_dict[target_aa] = [rule.modification_tag]

            # Apply modifications to sequence
            for i, (aa, site_mods) in enumerate(self.parsed_sequence):
                if aa in rule_dict:
                    if site_mods:
                        self.parsed_sequence[i] = (aa, site_mods + rule_dict[aa])
                    else:
                        self.parsed_sequence[i] = (aa, rule_dict[aa])

            # Remove fixed modifications
            self.properties["fixed_modifications"] = []


def _format_number_as_string(num):
    """Format number as string for ProForma mass modifications."""
    sign = "+" if np.sign(num) == 1 else "-"
    num = str(num).rstrip("0").rstrip(".")
    return sign + num


class PeptidoformException(PSMUtilsException):
    """Error while handling :py:class:`Peptidoform`."""

    pass


class AmbiguousResidueException(PeptidoformException):
    """Error while handling ambiguous residue."""

    pass


class ModificationException(PeptidoformException):
    """Error while handling amino acid modification."""

    pass
