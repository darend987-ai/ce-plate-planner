# CE Plate Planner

First Streamlit prototype for 3500 text layouts and the supplied 3600 CSV format.

## Run

Install Python 3.11 or later, then run these commands from this folder:

```
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Upload a tab-separated text layout. Drag samples or click a source and destination; occupied destinations swap samples. Edit plate settings and sample settings, then download the current CSV. Sample names are preserved unless edited. Files remain in the current Streamlit session; refreshing or closing the session can discard changes.

Output-only defaults come from the example CSV. Investigator 24Plex maps to InjectionProtocol INV24plex INST and RunModule1 INV24plex Inst. Source file-name convention and results group are not automatically mapped to the new instrument settings. Instrument acceptance still needs verification with your workflow. No sample-renaming rules have been added yet.

## GitHub and Streamlit

Upload this entire folder's contents to a GitHub repository, including the plate directory. Select app.py as the entry point in Streamlit Community Cloud. Do not commit private sample files. This prototype has no authentication or durable storage.


## Move a group

Hold the left mouse button and drag from an unselected well across the desired samples, then release to finish selecting. Click and hold any selected sample and drag it to its new well. Click an empty well to clear selection. No selection mode buttons are needed. Ctrl/Cmd-click adds or removes individual samples. The arrangement and empty gaps stay the same. Group moves must fit on the plate and cannot overlap unselected samples. A single sample can still swap with another sample. Escape clears the selection.



GlobalFiler maps to RunModule1 HID_J6_36_POP4 and InjectionProtocol HID_Protocol_J6_36_POP4.
GlobalFiler DyeSet is J6 (DS-36) and SizeStandard is GS600_LIZ_(60-460).

IdentiFiler Plus maps to InjectionProtocol HID_Protocol_G5_36_POP4, RunModule1 HID_G5_36_POP4, DyeSet G5 (DS-33), and SizeStandard GS600_LIZ_(60-460). Assay recognition ignores capitalization and surrounding spaces.


Choose Output assay above the upload field to use the source assay or convert all samples to Investigator 24Plex, GlobalFiler, or IdentiFiler Plus settings. Changing the choice updates injection protocol, run module, dye set and size standard while preserving current names, types and plate positions. Switching back restores source kit settings. It does not rename ladders or controls.

