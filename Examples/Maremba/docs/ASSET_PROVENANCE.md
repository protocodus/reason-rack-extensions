# Maremba asset provenance

This records where third-party panel art comes from. It is a traceability record,
not a legal conclusion or a grant of rights.

## Reason Studios stock decorations

The rear-panel routing symbols are the stock white icons from Reason Studios'
public 2D graphics pack, which the GUI design guidelines require on every back
panel. They are committed exactly as downloaded, byte-identical in `GUI2D/` and
`GUI/Output/HD/`, and copied from `Examples/YouKnow`, which records the same
hashes. `Design/render_panels.py` only composites them into the previews and
never re-encodes them. `Tests/validate_panel_geometry.py` fails if either file
changes.

| Stock pack input | SHA-256 | Maremba use |
| --- | --- | --- |
| `RE2D_Stock_Graphics_1_1.zip` from `https://cdn.reasonstudios.com/developers/RackExtensionSDK/Graphics/RE2D_Stock_Graphics_1_1.zip` | `3985d1aa9ccf3ff3752598146e9bb519510d0dd15dfc09b52110fc4a033f22c4` | - |
| `Decorations/Routing_Icon_White_01_1frames.png` (mono in, mono out) | `638b4b491632d4c3df9293943feb3f0faa2c61f840ae15f30e847cf80cdddc38` | beside the mono Piezo output (`S_routing_piezo`) |
| `Decorations/Routing_Icon_White_02_1frames.png` (mono in, stereo out) | `4bb34ecc958ac44c30f95298b2229a20800355f839f67c0012e96c00c8fe5f8a` | beside the Main, Close and Far stereo pairs (`S_routing_main`, `S_routing_close`, `S_routing_far`) |

Other files not rendered here:

- `PatchBrowseGroup.png` and `Placeholder.png` are byte-identical to the SDK examples'
  stock files (`Examples/SimpleInstrument/GUI2D`).
- `AudioJack.png`, `CVJack.png`, `TapeHorz.png`, `TapeVert.png`, `Lamp.png` and
  `Toggle.png` are byte-identical to `Examples/YouKnow/GUI2D`. That folder holds its
  re-encoded copies of the SDK's stock jacks and tapes, and its own lamp and toggle strips.

Every other image is rendered by `Design/render_panels.py` and `Design/render_knob.py`.
