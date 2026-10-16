"""The stable configuration interface; explicit compatibility exports only."""

from qmstrace.core.config._copy import (
    COPY_BEGIN as COPY_BEGIN,
)
from qmstrace.core.config._copy import (
    COPY_END as COPY_END,
)
from qmstrace.core.config._copy import (
    marked as marked,
)
from qmstrace.core.config._copy import (
    schema_digest as schema_digest,
)
from qmstrace.core.config._copy import (
    structural as structural,
)
from qmstrace.core.config._parse import (
    TraceConfig as TraceConfig,
)
from qmstrace.core.config._schema import (
    EXTRACTORS as EXTRACTORS,
)
from qmstrace.core.config._schema import (
    BaselineScope as BaselineScope,
)
from qmstrace.core.config._schema import (
    ChangeRequests as ChangeRequests,
)
from qmstrace.core.config._schema import (
    CoverageRule as CoverageRule,
)
from qmstrace.core.config._schema import (
    ExternalSource as ExternalSource,
)
from qmstrace.core.config._schema import (
    ItemType as ItemType,
)
from qmstrace.core.config._schema import (
    LinkType as LinkType,
)
from qmstrace.core.config._schema import (
    SchemaForm as SchemaForm,
)
from qmstrace.core.config._schema import (
    Subject as Subject,
)
from qmstrace.core.config._schema import (
    Tables as Tables,
)
from qmstrace.core.config._toml import (
    SUPPORTED_VERSION as SUPPORTED_VERSION,
)
