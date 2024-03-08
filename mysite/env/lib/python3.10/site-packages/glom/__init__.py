
from glom.core import (glom,
                       Fill,
                       Auto,
                       register,
                       Glommer,
                       Call,
                       Invoke,
                       Spec,
                       Ref,
                       OMIT,  # backwards compat
                       SKIP,
                       STOP,
                       UP,
                       ROOT,
                       MODE,
                       Path,
                       Vars,
                       Val,
                       Literal,  # backwards compat 2020-07
                       Let,  # backwards compat 2020-07
                       Coalesce,
                       Inspect,
                       Pipe,
                       GlomError,
                       BadSpec,
                       PathAccessError,
                       PathAssignError,
                       CoalesceError,
                       UnregisteredTarget,
                       T, S, A)

from glom.reduction import Sum, Fold, Flatten, flatten, FoldError, Merge, merge
from glom.matching import (M,
                           Or,
                           And,
                           Not,
                           Match,
                           MatchError,
                           TypeMatchError,
                           Regex,
                           Optional,
                           Required,
                           Switch,
                           Check,
                           CheckError)
from glom.mutation import Assign, Delete, assign, delete, PathDeleteError

# there's no -ion word that really fits what "streaming" means.
# generation, production, iteration, all have more relevant meanings
# elsewhere. (maybe procrastination :P)
from glom.streaming import Iter

from glom._version import __version__
