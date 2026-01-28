# Provision reference extraction

We use a formal grammar to extract provision-level citations from documents, such as "Section 2(a) of Act 42".
These extractions are run after the work-level extractions (such as "Act 5 of 2009") which means the provision
extraction can make use of that information to resolve the provision references.

The grammar is defined in `provision_refs.peg` and is compiled into Python (`provision_refs.py`) using
[Canopy](https://canopy.jcoglan.com/)

## Compiling changes

Install canopy:

```bash
npm install -g canopy
```

Compile the grammar:

```bash
canopy indigo/analysis/refs/provision_refs.peg --lang python
```

Run tests and commit the updated `provision_refs.py` file.
