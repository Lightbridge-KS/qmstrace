| Code | Kind | What is wrong |
|---|---|---|
| S01 | suspect | an existing local item downstream of changed or removed frozen content needs review |
| V01 | violation | an ID declared twice — in this repo, or already in a sibling |
| V02 | violation | an ID of this repo's kind that does not match its pattern |
| V03 | violation | a link to an ID that exists nowhere this run could read |
| V04 | violation | a link whose source or target is a kind of item the link type does not allow |
| V05 | violation | a required field missing, or a value outside its list |
| V06 | violation | a test with no level — not under a level folder |
| V07 | violation | an item declared in a file that is not scanned for its type |
| V08 | violation | a file that cannot be read or parsed |
| V09 | violation | an external ID its source does not declare |
| V10 | violation | a controlled item changed or added without a fresh change-request citation |
| V11 | violation | a cited change request does not exist, is malformed, or is not accepted |
| V12 | violation | a cited change request does not list the item under Impacts |
| V13 | violation | a frozen item's heading was removed |
| V14 | violation | a link field that holds something other than IDs |
| V15 | violation | a verifies marker in a form this tool does not read |
| V16 | violation | an ID of this repo's kind, declared nowhere, written where it declares nothing |
