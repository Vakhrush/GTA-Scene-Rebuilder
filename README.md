# GTA Scene Rebuilder

Blender addon for searching for and correctly placing GTA V props according to YTYP entity data.

The addon restores prop names when they are hashed and the original names are available.

Designed for workflows using Sollumz.

[Watch the tutorial on YouTube](https://youtu.be/mIBBfeaEZWw)

## Features

### Rebuild Scene

Rebuilds entity placement using existing props in the scene.

* Resolves hashed prop and archetype names using JOAAT hashes
* Restores original names when matching source names are available
* Searches for existing props in the scene
* Automatically links props to YTYP entities
* Reuses existing props when possible
* Creates duplicates when multiple entities use the same archetype
* Applies entity transforms
* Restores YTYP archetype asset references
* Does not import missing props

The project folder used for the original Sollumz import is required for resolving hashed names.

### Rebuild Props

Searches for missing props in the configured GTA Asset Library and Custom Props Library.

* Restores hashed prop names when original names are available
* Uses indexed asset lookup
* Supports JOAAT hash lookup
* Restores missing GTA V props from Asset Library (.blend files)
* Batch imports assets for improved performance
* Searches for custom props
* Imports custom props through Sollumz
* Automatically links props to YTYP entities
* Creates duplicates when multiple entities use the same archetype
* Applies entity transforms

### GTA Asset Restoration

* GTA V Asset Library support
* Indexed asset lookup
* Original filename lookup
* JOAAT hash lookup
* Batch asset importing
* Automatic entity linking
* Automatic duplication support

### Custom Props Support

* Recursive folder indexing
* Custom prop database
* JOAAT hash lookup
* Import through Sollumz
* Hierarchy reconstruction
* Automatic entity linking
* Automatic duplication support

### Scene Organization

Automatically creates:

* props_gta
* custom_props
* Hidden props
* Missing props

collections.

### Hide Non-YTYP Props

Moves unused Sollumz props into the "Hidden props" collection and hides the collection from viewport and render.

### Diagnostics

* Show Non-Linked Props button
* Missing entity reporting
* Console diagnostics and execution profiling

### Find Missing Props Here...

* Recursive folder search for other props
* Automatic entity relinking
* Hierarchy duplication support

## Requirements

* Blender 5.1+ (earlier versions have not been tested)
* Sollumz 2.8.3+ (earlier versions have not been tested)
* GTA5 Props Assets Library (.blend or other formats imported using Sollumz)

## Installation

1. Download the latest release ZIP.
2. Open Blender.
3. Edit → Preferences → Add-ons.
4. Click Install.
5. Select the ZIP archive.
6. Enable GTA Scene Rebuilder.

## Setup

### GTA Asset Library

Open addon preferences.

Set:

- Asset Library Path

Then click:

- Check and Build Asset Index

The index stores both original asset names and JOAAT hashes for hash-based lookup.

### Custom Props

Set:

- Custom Props Path

Then click:

- Check and Build Custom Props Index

The index stores both original prop names and JOAAT hashes for hash-based lookup.

## Usage

### Rebuild Scene

Use this tool when the YTYP entity data has already been imported through Sollumz and the required props already exist in the scene.

1. Import project assets through Sollumz.
2. Import YTYP using Sollumz.
3. Open:

- View3D → Sidebar → GTA Scene Rebuilder

4. Specify the project folder from which the Sollumz import was performed.
5. Click:

- Rebuild Scene

The addon will:

* resolve hashed YTYP names
* restore original prop names when available
* find matching props already present in the scene
* link props to YTYP entities
* reuse existing props when possible
* create duplicates when required
* apply entity transforms

### Rebuild Props

Use this tool when props referenced by YTYP entities are missing from the scene.

Click:

- Rebuild props

The addon will:

* search the configured GTA Asset Library and Custom Props Library
* resolve hashed prop names
* restore original names when available
* import missing props
* link props to YTYP entities
* create duplicates when required
* apply entity transforms

This operation may take some time depending on the size of the asset libraries.

### Hide Unused Props

Click:

- Hide Non-YTYP Props

Objects not referenced by YTYP entities will be moved to the "Hidden props" collection.

### Find Missing Props Here...

Use this tool when some entities remain unlinked after running Rebuild props.

Click:

1. Find Missing Props Here...
2. Select a folder containing custom props.

The addon will:

* recursively scan the selected folder
* find matching props by archetype name
* import props through Sollumz
* restore entity links
* apply entity transforms
* create hierarchy duplicates when required

Imported objects will be placed into the "Missing props" collection.

## Hash Resolution

GTA Scene Rebuilder supports resolving hashed prop and archetype names using JOAAT hashes.

For example:

`hash_7305e0f3`

can be resolved to its original prop name when the corresponding original name is present in the configured asset library or project source files.

Hash matching is case-insensitive and supports normalized 32-bit JOAAT values.

If an original name cannot be found, the hashed name is preserved.

## Performance

Current version uses:

* Asset indexing
* Custom props indexing
* JOAAT hash indexing
* Batch blend importing
* Existing object reuse
* Hierarchy duplication only when required

## Current Limitations

* Matching custom props relies on file naming.
* Hashed names can only be restored when the corresponding original name is available.
* Rebuild Scene requires the project folder used for the original Sollumz import to resolve source filenames.
* Asset indexes should be rebuilt after adding new assets.

---

## Roadmap

---

## Support

If GTA Scene Rebuilder has been useful for your projects and saved you time, you can support its future development.

➡️ See DONATE.md
