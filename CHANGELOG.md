# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2023-06-08

### Added
- Add reader for [Sage](https://github.com/lazear/sage) PSM files.
- `io.mzid`: Add reading/writing of PEP and q-values

### Changed
- `psm`: The default values of `PSM.provenance_data`, `PSM.metadata` and `PSM.rescoring_features` are now `dict()` instead of `None`.
- `PSMList`: Also allow Numpy integers for indexing a single PSM
- `io.mzid.MzidReader`: Attempt to parse `retention time` or `scan start time` cvParams from both SpectrumIdentificationResult as SpectrumIdentificationItem levels. Note that according to the mzIdentML specification document (v1.1.1) neither cvParams are expected to be present at either level.
- `io.mzid.MzidReader`: Prefer `spectrum title` cvParam over `spectrumID` attribute for `PSM.spectrum_id` as these titles always match to the peak list files. In this case, `spectrumID` is saved in `metadata["mzid_spectrum_id"]`. Fall back to `spectrumID` if `spectrum title` is absent.
- `io.mzid.MzidWriter`: `PSM.retention_time` is now written as cvParam `retention time` instead of `scan start time`, and to the `SpectrumIdentificationItem` level instead of the `SpectrumIdentificationResult` level, as theoretically in psm_utils, multiple PSMs for the same spectrum can have different values for `retention_time`.
- `io.mzid.MzidWriter`: Write PSM score as cvParam `search engine specific score` instead of userParam `score`.
- `io.percolator.PercolatorTabWriter`: For PIN-style files: Use `SpecId` instead of `PSMId` and write `PSMScore` and `ChargeN` columns by default.
- Filter warnings from `psims.mzmlb` on import, as `mzmlb` is not used

### Fixed
- `psm`: Fix missing qvalue and pep in docstring
- `peptidoform`: ProForma mass modifications are now correctly parsed within the `rename_modifications` function.
- `io.maxquant.MSMSReader`: Correctly parse empty `Proteins` column to `None`
- `io.percolator.PercolatorTabReader`: Correctly parse Percolator peptidoform notation if no leading or trailing amino acids are present (e.g. `.ACDK.` instead of `K.ACDK.E`).
- `io.percolator.PercolatorTabWriter`: ScanNr is now correctly written as an integer counting from the first PSM in the file.
- `io.percolator.PercolatorTabWriter`: If no protein information is present, write the peptidoform preceded by `PEP_` to the Proteins column.
- `io.idxml`: Read metadata as strings
- `io.mzid.MzidReader`: Set `PSM.retention_time` to `None` instead of `float('nan')` if missing from the PSM file.
- `io.mzid`: Fix reading of file if charge is missing
- `io.mzid`: Fix writing if protein_list is None
- `io.mzid`: Consider all `PeptideEvidence` entries for a `SpectrumIdentificationItem` to determine `is_decoy`
- `io.mzid`: Fix handling of mzIdentML files when `is_decoy` field is not present (fixes #30)
- `io.tsv`: Raise `PSMUtilsIOException` with clear error message when TSV `protein_list` cannot be read

## [0.2.3] - 2023-03-08

### Fixed

- Fix bug in `io._base_classes` (introduced in v0.2.2)
- Fix bug in TSVReader for reading TSV files with empty protein_list

## [0.2.2] - 2023-03-08

### Fixed

- `io.peptide_record`: Fix bug where provenance item `filename` was not a string
- Various minor fixes after linting

## [0.2.1] - 2023-01-17

### Added

- `Peptidoform`: Add `is_modified` property

### Fixed

- `io.mzid`: Fix issues when parsing Comet or MSAmanda-generated mzIdentML files and certain fields are missing.

## [0.2.0] - 2022-11-12

### Added

- `PSM`: Add `ion_mobility` field
- `PSMList`: Allow slicing with bool arrays (e.g., `psm_df[psm_df["retention_time"] < 2000]`)
- `rename_modifications`: Add support for fixed modifications
- Add example files
- Online: Add support for GZipped files
- Online: Add support for logarithmic score (e.g. e-values)
- Docs: Extend contributing with example contributions
- Docs: Add notes to `PSM.get_usi()` method
- Docs: Extend quickstart on PSMList
- Docs: Add "psm_utils tags" for file formats, as used in high-level read/write/convert functions
- Docs: Peptide Record: add notes on unsupported modification types; add example for C-terminal modification
- Docs: More clearly document conversion to DataFrame
- Docs: Add bioconda install instructions
- Docs: Add citation for preprint
- Tests: Added tests for PSMList `set_ranks` and `get_rank1_psms` methods

### Changed

- `PSMList`: Refactor `set_ranks` and `get_rank1_psms` methods
- Update `.vscode/settings.json`
- Typing: Replace Union with OR operator `|`
- Online: Use percentiles instead of randomly sampling for PP plot
- Docs: Force TOC-tree max depth
- Tests: Expand unit tests in general

### Fixed

- `PSMList`: Truncate __repr__ to first five entries only, avoiding crashing notebook output
- `Peptidoform`: Minor typing fix
- `add_fixed_modifications`: Allow input as dict as well as list of tuples
- `io`: Fix issue where the `NamedTemporaryFile` for `_supports_write_psm` was seen as invalid Percolator file
- `io.convert`: pass ` progressbar` argument to class, not `write_file`
- `io.mzid`: Add more supported MS-GF score names, make SpecEValue default
- `io.peptide_record`: `spec_id` is now a required column (`spectrum_id` is also required in PSM)
- `io.peptide_record`: Fix parsing of C-terminal modifications from proforma to peprec
- `io.percolator`: Fix Percolator peptide notation writing (fixes #18)
- `io.tsv`: Fix issue where `TSVReader` would not use string type for metadata
- `io.xtandem`: Fix issue where optional arguments were not accepted by `XTandemReader`
- `io.xtandem`: Do not split spectrum title on space
- `io.xtandem`: Fix issue where optional arguments were not accepted by `XTandemReader`
- Online: Fix pi-0 diagonal calculation
- Remove obsolete to do comments in code

## [0.1.0] - 2022-10-14

### Added

- Initial version
