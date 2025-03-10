import unittest
from collections import OrderedDict

from conans.test.utils.tools import NO_SETTINGS_PACKAGE_ID, TestClient, TestServer


class RemoteChecksTest(unittest.TestCase):

    def test_binary_defines_remote(self):
        servers = OrderedDict([("server1", TestServer()),
                               ("server2", TestServer()),
                               ("server3", TestServer())])
        client = TestClient(servers=servers, inputs=3*["admin", "password"])
        conanfile = """from conan import ConanFile
class Pkg(ConanFile):
    pass"""
        client.save({"conanfile.py": conanfile})
        client.run("create . --name=pkg --version=0.1 --user=lasote --channel=testing")
        client.run("upload pkg* -r=server1 --confirm")
        client.run("upload pkg* -r=server2 --confirm")

        # It takes the default remote
        client.run("remove * -c")

        # Exported recipe gets binary from default remote
        client.run("export . --name=pkg --version=0.1 --user=lasote --channel=testing")
        client.run("install --requires=pkg/0.1@lasote/testing")
        client.assert_listed_binary(
            {"pkg/0.1@lasote/testing": (NO_SETTINGS_PACKAGE_ID, "Download (server1)")})
        self.assertIn("pkg/0.1@lasote/testing: Retrieving package "
                      "%s from remote 'server1'" % NO_SETTINGS_PACKAGE_ID, client.out)

        # Explicit remote also defines the remote
        client.run("remove * -c")
        client.run("export . --name=pkg --version=0.1 --user=lasote --channel=testing")
        client.run("install --requires=pkg/0.1@lasote/testing -r=server2")
        client.assert_listed_binary(
            {"pkg/0.1@lasote/testing": (NO_SETTINGS_PACKAGE_ID, "Download (server2)")})
        self.assertIn("pkg/0.1@lasote/testing: Retrieving package "
                      "%s from remote 'server2'" % NO_SETTINGS_PACKAGE_ID, client.out)

        # Ordered search of binary works
        client.run("remove * -c")
        client.run("remove * -c -r=server1")
        client.run("export . --name=pkg --version=0.1 --user=lasote --channel=testing")
        client.run("install --requires=pkg/0.1@lasote/testing")
        client.assert_listed_binary(
            {"pkg/0.1@lasote/testing": (NO_SETTINGS_PACKAGE_ID, "Download (server2)")})
        self.assertIn("pkg/0.1@lasote/testing: Retrieving package "
                      "%s from remote 'server2'" % NO_SETTINGS_PACKAGE_ID, client.out)

        # Download recipe and binary from the remote2 by iterating
        client.run("remove * -c")
        client.run("remove * -c -r=server1")
        client.run("install --requires=pkg/0.1@lasote/testing")
        client.assert_listed_binary(
            {"pkg/0.1@lasote/testing": (NO_SETTINGS_PACKAGE_ID, "Download (server2)")})
        self.assertIn("pkg/0.1@lasote/testing: Retrieving package "
                      "%s from remote 'server2'" % NO_SETTINGS_PACKAGE_ID, client.out)

    def test_binaries_from_different_remotes(self):
        servers = OrderedDict()
        servers["server1"] = TestServer()
        servers["server2"] = TestServer()
        client = TestClient(servers=servers, inputs=2*["admin", "password"])
        conanfile = """from conan import ConanFile
class Pkg(ConanFile):
    options = {"opt": [1, 2, 3]}
"""
        client.save({"conanfile.py": conanfile})
        client.run("create . --name=pkg --version=0.1 --user=lasote --channel=testing -o pkg/*:opt=1")
        client.run("upload pkg* -r=server1 --confirm")
        client.run("remove *:* -c")
        client.run("create . --name=pkg --version=0.1 --user=lasote --channel=testing -o pkg/*:opt=2")
        package_id2 = client.created_package_id("pkg/0.1@lasote/testing")
        client.run("upload pkg* -r=server2 --confirm")
        client.run("remove *:* -c")

        # recipe is cached, takes binary from server2
        client.run("install --requires=pkg/0.1@lasote/testing -o pkg/*:opt=2 -r=server2")
        client.assert_listed_binary({"pkg/0.1@lasote/testing": (package_id2, "Download (server2)")})
        self.assertIn(f"pkg/0.1@lasote/testing: Retrieving package {package_id2} "
                      "from remote 'server2'", client.out)

        # Nothing to update
        client.run("install --requires=pkg/0.1@lasote/testing -o pkg/*:opt=2 -r=server2 -u")
        client.assert_listed_binary({"pkg/0.1@lasote/testing": (package_id2, "Cache")})

        # Build missing
        client.run("install --requires=pkg/0.1@lasote/testing -o pkg/*:opt=3 -r=server2", assert_error=True)
        self.assertIn("ERROR: Missing prebuilt package for 'pkg/0.1@lasote/testing'", client.out)

        client.run("install --requires=pkg/0.1@lasote/testing -o pkg/*:opt=3", assert_error=True)
        self.assertIn("ERROR: Missing prebuilt package for 'pkg/0.1@lasote/testing'", client.out)
