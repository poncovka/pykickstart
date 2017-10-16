import unittest
import warnings
from tests.baseclass import CommandTest, ParserTest

from pykickstart.constants import KS_MISSING_IGNORE
from pykickstart.errors import KickstartParseError, KickstartValueError
from pykickstart.parser import Group, Packages
from pykickstart.version import DEVEL, F21, RHEL6, returnClassForVersion

class DevelPackagesBase(CommandTest):
    @property
    def handler(self):
        return returnClassForVersion(DEVEL)

class AddGlobs_TestCase(DevelPackagesBase):
    def runTest(self):
        pkgs = Packages()
        pkgs.add(["vim-*"])
        pkgs.add(["kde*"])

        self.assertEqual("""%packages
kde*
vim-*

%end""", str(pkgs).strip())

class AddGroups_TestCase(DevelPackagesBase):
    def runTest(self):
        pkgs = Packages()
        pkgs.add(["@GroupA"])
        pkgs.add(["@group-b"])
        pkgs.add(["@GroupC"])

        # Groups are printed out in alphabetic order, so group-b comes after Group*
        self.assertEqual("""%packages
@GroupA
@GroupC
@group-b

%end""", str(pkgs).strip())

        pkgs = Packages()
        pkgs.add(["@group-a --nodefaults"])
        self.assertEqual("""%packages
@group-a --nodefaults

%end""", str(pkgs).strip())

        pkgs = Packages()
        pkgs.add(["@group-a --optional"])
        self.assertEqual("""%packages
@group-a --optional

%end""", str(pkgs).strip())

        self.assertRaises(KickstartValueError, pkgs.add, ["@group-b --optional --nodefaults"])

class AddGroupsAndEnvironment_TestCase(DevelPackagesBase):
    def runTest(self):
        pkgs = Packages()
        pkgs.add(["@^EnvironmentA"])
        pkgs.add(["@GroupB"])
        pkgs.add(["packageC"])

        self.assertEqual("""%packages
@^EnvironmentA
@GroupB
packageC

%end""", str(pkgs).strip())

class AddPackages_TestCase(DevelPackagesBase):
    def runTest(self):
        pkgs = Packages()
        pkgs.add(["packageA"])
        pkgs.add(["packageB"])
        pkgs.add(["packageC"])

        self.assertEqual("""%packages
packageA
packageB
packageC

%end""", str(pkgs).strip())

class ExcludeGlobs_TestCase(DevelPackagesBase):
    def runTest(self):
        pkgs = Packages()
        pkgs.add(["-kde*"])
        pkgs.add(["-perl*"])
        pkgs.add(["-*spell"])

        self.assertEqual("""%packages
-*spell
-kde*
-perl*

%end""", str(pkgs).strip())

class ExcludeGroups_TestCase(DevelPackagesBase):
    def runTest(self):
        pkgs = Packages()
        pkgs.add(["-@Conflicts"])
        pkgs.add(["-@Clustering"])

        self.assertEqual("""%packages
-@Clustering
-@Conflicts

%end""", str(pkgs).strip())

class ExcludePackage_TestCase(DevelPackagesBase):
    def runTest(self):
        pkgs = Packages()
        pkgs.add(["-enlightenment"])
        pkgs.add(["-clanlib"])
        pkgs.add(["-libass"])

        self.assertEqual("""%packages
-clanlib
-enlightenment
-libass

%end""", str(pkgs).strip())

class Mixed1_TestCase(DevelPackagesBase):
    def runTest(self):
        pkgs = Packages()
        pkgs.add(["@group-a"])
        pkgs.add(["@group-b"])
        pkgs.add(["-@group-a"])

        self.assertEqual("""%packages
@group-b
-@group-a

%end""", str(pkgs).strip())

class Mixed2_TestCase(DevelPackagesBase):
    def runTest(self):
        pkgs = Packages()
        pkgs.add(["vim-enhanced"])
        pkgs.add(["package-b"])
        pkgs.add(["-vim-enhanced"])

        self.assertEqual("""%packages
package-b
-vim-enhanced

%end""", str(pkgs).strip())

class Mixed3_TestCase(DevelPackagesBase):
    def runTest(self):
        pkgs = Packages()
        pkgs.add(["vim-enhanced"])
        pkgs.add(["package-b"])
        pkgs.add(["-vim*"])

        self.assertEqual("""%packages
package-b
vim-enhanced
-vim*

%end""", str(pkgs).strip())

class MultiLib_TestCase(DevelPackagesBase):
    def runTest(self):
        pkgs = Packages()
        pkgs.default = True
        pkgs.multiLib = True
        self.assertEqual("""%packages --default --multilib

%end""", str(pkgs).strip())

class GroupsAreHashable_TestCase(ParserTest):
    def runTest(self):
        hash(Group(name="groupA"))

class Packages_Options_TestCase(ParserTest):
    ks = """
%packages --ignoremissing --default --instLangs="bg_BG"
%end
"""

    def runTest(self):
        self.parser.readKickstartFromString(self.ks)

        # Verify that the options are parsed as expected
        self.assertTrue(self.handler.packages.default)
        self.assertEqual(self.handler.packages.handleMissing, KS_MISSING_IGNORE)
        self.assertEqual(self.handler.packages.instLangs, "bg_BG")

        # extra test coverage
        self.assertTrue(self.parser._sections['%packages'].seen)

class Packages_Options_Empty_InstLangs_TestCase(ParserTest):
    ks = """
%packages --instLangs=
%end
"""

    def runTest(self):
        self.parser.readKickstartFromString(self.ks)

        # Verify that instLangs is an empty string
        self.assertEqual(self.handler.packages.instLangs, "")

        # Verify that the empty instLangs comes back out
        self.assertEqual(str(self.handler.packages).strip(), "%packages --instLangs=\n\n%end")

class Packages_Options_No_InstLangs_TestCase(ParserTest):
    ks = """
%packages
%end
"""

    def runTest(self):
        self.parser.readKickstartFromString(self.ks)

        # Verify that instLangs is None
        self.assertIsNone(self.handler.packages.instLangs)

        # Verify that --instLangs is not displayed
        self.assertEqual(str(self.handler.packages).strip(), "%packages\n\n%end")

class Packages_Contains_Comments_TestCase(ParserTest):
    ks = """
%packages
packageA    # this is an end-of-line comment
# this is a whole line comment
packageB
packageC
%end
"""

    def runTest(self):
        self.parser.readKickstartFromString(self.ks)

        # Verify that the packages are what we think they are.
        self.assertEqual(len(self.handler.packages.packageList), 3)
        self.assertEqual(self.handler.packages.packageList[0], "packageA")
        self.assertEqual(self.handler.packages.packageList[1], "packageB")
        self.assertEqual(self.handler.packages.packageList[2], "packageC")

class Packages_Contains_Nobase_1_TestCase(ParserTest):
    version = F21

    ks = """
%packages --nobase
bash
%end
"""

    def runTest(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warnings.simplefilter("ignore", PendingDeprecationWarning)
            self.parser.readKickstartFromString(self.ks)
            self.assertEqual(len(w), 1)
            self.assertIsInstance(w[-1].message, DeprecationWarning)

class Packages_Contains_Nobase_2_TestCase(ParserTest):
    version = RHEL6

    ks = """
%packages --nobase
bash
%end
"""

    def runTest(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warnings.simplefilter("ignore", PendingDeprecationWarning)
            self.parser.readKickstartFromString(self.ks)
            self.assertEqual(len(w), 0)

class Packages_Contains_Nobase_3_TestCase(ParserTest):
    ks = """
%packages --nobase
bash
%end
"""

    def runTest(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            self.assertRaises(KickstartParseError, self.parser.readKickstartFromString, self.ks)

class Packages_Contains_Nobase_Default_TestCase(ParserTest):
    version = F21

    ks = """
%packages --nobase --default
%end
"""

    def runTest(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            self.assertRaises(KickstartParseError, self.parser.readKickstartFromString, self.ks)

class Packages_Contains_Nocore_Default_TestCase(ParserTest):
    ks = """
%packages --nocore --default
%end
"""

    def runTest(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            self.assertRaises(KickstartParseError, self.parser.readKickstartFromString, self.ks)

class Packages_Contains_Environment_1_TestCase(ParserTest):
    ks = """
%packages
@^whatever-environment
%end
"""

    def runTest(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            self.parser.readKickstartFromString(self.ks)
            self.assertEqual(self.handler.packages.environment, "whatever-environment")

class Packages_Contains_Environment_2_TestCase(ParserTest):
    ks = """
%packages
@^whatever-environment
@^another-environment
%end
"""

    def runTest(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            self.parser.readKickstartFromString(self.ks)
            self.assertEqual(self.handler.packages.environment, "another-environment")

class Packages_Contains_Environment_3_TestCase(ParserTest):
    ks = """
%packages
@^whatever-environment
-@^another-environment
%end
"""

    def runTest(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            self.parser.readKickstartFromString(self.ks)
            self.assertEqual(self.handler.packages.environment, "whatever-environment")

class Packages_Contains_Environment_4_TestCase(ParserTest):
    ks = """
%packages
@^whatever-environment
-@^whatever-environment
@^another-environment
%end
"""

    def runTest(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            self.parser.readKickstartFromString(self.ks)
            self.assertEqual(self.handler.packages.environment, "another-environment")

# An empty %packages section is allowed, and means something different from %packages --default.
# An empty section means to install the minimum amount of stuff, while --default means to install
# whatever would have been installed had this been a graphical installation and the user just
# accepted whatever was offered.
class Packages_Empty_TestCase(ParserTest):
    ks = """
%packages
%end
"""

    def runTest(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            self.parser.readKickstartFromString(self.ks)
            self.assertTrue(self.handler.packages.seen)
            self.assertEqual(str(self.handler.packages).strip(), "%packages\n\n%end")

class WeakDeps_TestCase(DevelPackagesBase):
    def runTest(self):
        pkgs = Packages()
        pkgs.default = True
        pkgs.excludeWeakdeps = True
        self.assertEqual("""%packages --default --excludeWeakdeps

%end""", str(pkgs).strip())

class Packages_Timeout_TestCase(DevelPackagesBase):
    def runTest(self):
        pkgs = Packages()
        pkgs.add(["test"])
        pkgs.timeout = 60
        self.assertEqual("""%packages --timeout=60
test

%end""", str(pkgs).strip())
        pkgs.timeout = None
        self.assertEqual("""%packages
test

%end""", str(pkgs).strip())

class Packages_Retries_TestCase(DevelPackagesBase):
    def runTest(self):
        pkgs = Packages()
        pkgs.add(["test"])
        pkgs.retries = 10
        self.assertEqual("""%packages --retries=10
test

%end""", str(pkgs).strip())
        pkgs.retries = None
        self.assertEqual("""%packages
test

%end""", str(pkgs).strip())


if __name__ == "__main__":
    unittest.main()
