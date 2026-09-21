# What ships with the engine

Files in this folder are package data: they travel inside the wheel and are read at run time
with `importlib.resources`. The skill an agent loads in a traced repo, the stanza written
into a product repo's agent guide, and the templates `init` uses all live here.

A test reads this file back from the installed package, and the pipeline reads it back from
the built wheel — data files missing from a wheel is a classic late surprise.
