# Fusion API notes

No Autodesk API integration has been implemented or run. No API assumptions
have been verified yet. The first task deliberately introduces no `adsk` imports.

Before implementing adapters, verify against current official Autodesk API
documentation: construction-axis geometry in root/occurrence coordinates,
internal length units, component transforms, sketch/profile creation, extrusion,
command lifecycle and event-handler cleanup. Record sources and runtime findings
here. Keep version-sensitive behavior in `fusion`.
