import os
import textwrap

from conans.test.assets.genconanfile import GenConanfile
from conans.test.utils.tools import TestClient
from conans.util.files import save


def test_settings_user():
    c = TestClient()
    settings_user = textwrap.dedent("""\
        os:
            Windows:
                subsystem: [new_sub]
            Linux:
                new_versions: ["a", "b", "c"]
            new_os:
        new_global: ["42", "21"]
        """)
    save(os.path.join(c.cache_folder, "settings_user.yml"), settings_user)
    c.save({"conanfile.py": GenConanfile().with_settings("os").with_settings("new_global")})
    # New settings are there
    c.run("install . -s os=Windows -s os.subsystem=new_sub -s new_global=42")
    assert "new_global=42" in c.out
    assert "os.subsystem=new_sub" in c.out
    # Existing values of subsystem are still there
    c.run("install . -s os=Windows -s os.subsystem=msys2 -s new_global=42")
    assert "new_global=42" in c.out
    assert "os.subsystem=msys2" in c.out
    # Completely new values, not appended, but new, are there
    c.run("install . -s os=Linux -s os.new_versions=a -s new_global=42")
    assert "new_global=42" in c.out
    assert "os.new_versions=a" in c.out
    # Existing values of OSs are also there
    c.run("install . -s os=Macos -s new_global=42")
    assert "os=Macos" in c.out
    assert "new_global=42" in c.out


def test_settings_user_subdict():
    c = TestClient()
    settings_user = textwrap.dedent("""\
        other_new:
            other1:
            other2:
                version: [1, 2, 3]
        """)
    save(os.path.join(c.cache_folder, "settings_user.yml"), settings_user)
    c.save({"conanfile.py": GenConanfile().with_settings("other_new")})
    c.run("install . -s other_new=other1")
    assert "other_new=other1" in c.out
    c.run("install . -s other_new=other2 -s other_new.version=2")
    assert "other_new=other2" in c.out
    assert "other_new.version=2" in c.out
