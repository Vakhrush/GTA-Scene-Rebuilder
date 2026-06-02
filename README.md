# GTA Scene Rebuilder

Blender addon for restoring GTA V scenes from YTYP entity data.

Designed for workflows using Sollumz.

## Features

### Analyze Scene

Scans imported YTYP data and detects:

* Missing entity references
* Missing GTA props
* Missing custom props
* Duplicate entity setups

### GTA Asset Restoration

* Restores missing GTA V props from Asset Library (.blend files)
* Uses indexed asset lookup
* Batch imports assets for improved performance
* Creates duplicates when multiple entities use the same archetype
* Automatically links imported objects to YTYP entities
* Applies entity transforms

### Custom Props Support

* Recursive folder indexing
* Custom prop database
* Import through Sollumz
* Hierarchy reconstruction
* Automatic entity linking
* Automatic duplication support

### Scene Organization

Automatically creates:

* props_gta
* custom_props
* Hidden props

collections.

### Hide Non-YTYP Props

Moves scene objects not referenced by any YTYP entity into:

  Hidden props

and hides them from viewport and render.

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

-Asset Library Path

Then click:

-Check and Build Asset Index

### Custom Props

Set:

-Custom Props Path

Then click:

-Check and Build Custom Props Index

## Usage

### Restore Scene

1. Import project assets.
2. Import YTYP using Sollumz.
3. Open:

-View3D → Sidebar → GTA Scene Rebuilder

4. Click:

-Analyze Scene

The addon will:

* restore missing GTA props
* restore custom props
* rebuild entity links
* create duplicates when required
* apply transforms automatically

### Hide Unused Props

Click:

-Hide Non-YTYP Props

Objects not referenced by YTYP entities will be moved to Hidden props.

## Performance

Current version uses:

* Asset indexing
* Custom props indexing
* Batch blend importing

