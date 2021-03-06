# Copyright 2013-2016 The Meson development team

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import sys, struct

SHT_STRTAB = 3
DT_NEEDED = 1
DT_RPATH = 15
DT_RUNPATH = 29
DT_STRTAB = 5
DT_SONAME = 14
DT_MIPS_RLD_MAP_REL = 1879048245

class DataSizes:
    def __init__(self, ptrsize, is_le):
        if is_le:
            p = '<'
        else:
            p = '>'
        self.Half = p + 'h'
        self.HalfSize = 2
        self.Word = p + 'I'
        self.WordSize = 4
        self.Sword = p + 'i'
        self.SwordSize = 4
        if ptrsize == 64:
            self.Addr = p + 'Q'
            self.AddrSize = 8
            self.Off = p + 'Q'
            self.OffSize = 8
            self.XWord = p + 'Q'
            self.XWordSize = 8
            self.Sxword = p + 'q'
            self.SxwordSize = 8
        else:
            self.Addr = p + 'I'
            self.AddrSize = 4
            self.Off = p + 'I'
            self.OffSize = 4

class DynamicEntry(DataSizes):
    def __init__(self, ifile, ptrsize, is_le):
        super().__init__(ptrsize, is_le)
        self.ptrsize = ptrsize
        if ptrsize == 64:
            self.d_tag = struct.unpack(self.Sxword, ifile.read(self.SxwordSize))[0]
            self.val = struct.unpack(self.XWord, ifile.read(self.XWordSize))[0]
        else:
            self.d_tag = struct.unpack(self.Sword, ifile.read(self.SwordSize))[0]
            self.val = struct.unpack(self.Word, ifile.read(self.WordSize))[0]

    def write(self, ofile):
        if self.ptrsize == 64:
            ofile.write(struct.pack(self.Sxword, self.d_tag))
            ofile.write(struct.pack(self.XWord, self.val))
        else:
            ofile.write(struct.pack(self.Sword, self.d_tag))
            ofile.write(struct.pack(self.Word, self.val))

class SectionHeader(DataSizes):
    def __init__(self, ifile, ptrsize, is_le):
        super().__init__(ptrsize, is_le)
        if ptrsize == 64:
            is_64 = True
        else:
            is_64 = False
# Elf64_Word
        self.sh_name = struct.unpack(self.Word, ifile.read(self.WordSize))[0]
# Elf64_Word
        self.sh_type = struct.unpack(self.Word, ifile.read(self.WordSize))[0]
# Elf64_Xword
        if is_64:
            self.sh_flags = struct.unpack(self.XWord, ifile.read(self.XWordSize))[0]
        else:
            self.sh_flags = struct.unpack(self.Word, ifile.read(self.WordSize))[0]
# Elf64_Addr
        self.sh_addr = struct.unpack(self.Addr, ifile.read(self.AddrSize))[0]
# Elf64_Off
        self.sh_offset = struct.unpack(self.Off, ifile.read(self.OffSize))[0]
# Elf64_Xword
        if is_64:
            self.sh_size = struct.unpack(self.XWord, ifile.read(self.XWordSize))[0]
        else:
            self.sh_size = struct.unpack(self.Word, ifile.read(self.WordSize))[0]
# Elf64_Word
        self.sh_link = struct.unpack(self.Word, ifile.read(self.WordSize))[0]
# Elf64_Word
        self.sh_info = struct.unpack(self.Word, ifile.read(self.WordSize))[0]
# Elf64_Xword
        if is_64:
            self.sh_addralign = struct.unpack(self.XWord, ifile.read(self.XWordSize))[0]
        else:
            self.sh_addralign = struct.unpack(self.Word, ifile.read(self.WordSize))[0]
#Elf64_Xword
        if is_64:
            self.sh_entsize = struct.unpack(self.XWord, ifile.read(self.XWordSize))[0]
        else:
            self.sh_entsize = struct.unpack(self.Word, ifile.read(self.WordSize))[0]

class Elf(DataSizes):
    def __init__(self, bfile, verbose=True):
        self.bfile = bfile
        self.verbose = verbose
        self.bf = open(bfile, 'r+b')
        try:
            (self.ptrsize, self.is_le) = self.detect_elf_type()
            super().__init__(self.ptrsize, self.is_le)
            self.parse_header()
            self.parse_sections()
            self.parse_dynamic()
        except:
            self.bf.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.bf.close()

    def detect_elf_type(self):
        data = self.bf.read(6)
        if data[1:4] != b'ELF':
            # This script gets called to non-elf targets too
            # so just ignore them.
            if self.verbose:
                print('File "%s" is not an ELF file.' % self.bfile)
            sys.exit(0)
        if data[4] == 1:
            ptrsize = 32
        elif data[4] == 2:
            ptrsize = 64
        else:
            sys.exit('File "%s" has unknown ELF class.' % self.bfile)
        if data[5] == 1:
            is_le = True
        elif data[5] == 2:
            is_le = False
        else:
            sys.exit('File "%s" has unknown ELF endianness.' % self.bfile)
        return ptrsize, is_le

    def parse_header(self):
        self.bf.seek(0)
        self.e_ident = struct.unpack('16s', self.bf.read(16))[0]
        self.e_type = struct.unpack(self.Half, self.bf.read(self.HalfSize))[0]
        self.e_machine = struct.unpack(self.Half, self.bf.read(self.HalfSize))[0]
        self.e_version = struct.unpack(self.Word, self.bf.read(self.WordSize))[0]
        self.e_entry = struct.unpack(self.Addr, self.bf.read(self.AddrSize))[0]
        self.e_phoff = struct.unpack(self.Off, self.bf.read(self.OffSize))[0]
        self.e_shoff = struct.unpack(self.Off, self.bf.read(self.OffSize))[0]
        self.e_flags = struct.unpack(self.Word, self.bf.read(self.WordSize))[0]
        self.e_ehsize = struct.unpack(self.Half, self.bf.read(self.HalfSize))[0]
        self.e_phentsize = struct.unpack(self.Half, self.bf.read(self.HalfSize))[0]
        self.e_phnum = struct.unpack(self.Half, self.bf.read(self.HalfSize))[0]
        self.e_shentsize = struct.unpack(self.Half, self.bf.read(self.HalfSize))[0]
        self.e_shnum = struct.unpack(self.Half, self.bf.read(self.HalfSize))[0]
        self.e_shstrndx = struct.unpack(self.Half, self.bf.read(self.HalfSize))[0]

    def parse_sections(self):
        self.bf.seek(self.e_shoff)
        self.sections = []
        for i in range(self.e_shnum):
            self.sections.append(SectionHeader(self.bf, self.ptrsize, self.is_le))

    def read_str(self):
        arr = []
        x = self.bf.read(1)
        while x != b'\0':
            arr.append(x)
            x = self.bf.read(1)
            if x == b'':
                raise RuntimeError('Tried to read past the end of the file')
        return b''.join(arr)

    def find_section(self, target_name):
        section_names = self.sections[self.e_shstrndx]
        for i in self.sections:
            self.bf.seek(section_names.sh_offset + i.sh_name)
            name = self.read_str()
            if name == target_name:
                return i

    def parse_dynamic(self):
        sec = self.find_section(b'.dynamic')
        self.dynamic = []
        if sec is None:
            return
        self.bf.seek(sec.sh_offset)
        while True:
            e = DynamicEntry(self.bf, self.ptrsize, self.is_le)
            self.dynamic.append(e)
            if e.d_tag == 0:
                break

    def print_section_names(self):
        section_names = self.sections[self.e_shstrndx]
        for i in self.sections:
            self.bf.seek(section_names.sh_offset + i.sh_name)
            name = self.read_str()
            print(name.decode())

    def print_soname(self):
        soname = None
        strtab = None
        for i in self.dynamic:
            if i.d_tag == DT_SONAME:
                soname = i
            if i.d_tag == DT_STRTAB:
                strtab = i
        if soname is None or strtab is None:
            print("This file does not have a soname")
            return
        self.bf.seek(strtab.val + soname.val)
        print(self.read_str())

    def get_entry_offset(self, entrynum):
        sec = self.find_section(b'.dynstr')
        for i in self.dynamic:
            if i.d_tag == entrynum:
                return sec.sh_offset + i.val
        return None

    def print_rpath(self):
        offset = self.get_entry_offset(DT_RPATH)
        if offset is None:
            print("This file does not have an rpath.")
        else:
            self.bf.seek(offset)
            print(self.read_str())

    def print_runpath(self):
        offset = self.get_entry_offset(DT_RUNPATH)
        if offset is None:
            print("This file does not have a runpath.")
        else:
            self.bf.seek(offset)
            print(self.read_str())

    def print_deps(self):
        sec = self.find_section(b'.dynstr')
        deps = []
        for i in self.dynamic:
            if i.d_tag == DT_NEEDED:
                deps.append(i)
        for i in deps:
            offset = sec.sh_offset + i.val
            self.bf.seek(offset)
            name = self.read_str()
            print(name)

    def fix_deps(self, prefix):
        sec = self.find_section(b'.dynstr')
        deps = []
        for i in self.dynamic:
            if i.d_tag == DT_NEEDED:
                deps.append(i)
        for i in deps:
            offset = sec.sh_offset + i.val
            self.bf.seek(offset)
            name = self.read_str()
            if name.startswith(prefix):
                basename = name.split(b'/')[-1]
                padding = b'\0' * (len(name) - len(basename))
                newname = basename + padding
                assert(len(newname) == len(name))
                self.bf.seek(offset)
                self.bf.write(newname)

    def fix_rpath(self, new_rpath):
        # The path to search for can be either rpath or runpath.
        # Fix both of them to be sure.
        self.fix_rpathtype_entry(new_rpath, DT_RPATH)
        self.fix_rpathtype_entry(new_rpath, DT_RUNPATH)

    def fix_rpathtype_entry(self, new_rpath, entrynum):
        if isinstance(new_rpath, str):
            new_rpath = new_rpath.encode('utf8')
        rp_off = self.get_entry_offset(entrynum)
        if rp_off is None:
            if self.verbose:
                print('File does not have rpath. It should be a fully static executable.')
            return
        self.bf.seek(rp_off)
        old_rpath = self.read_str()
        if len(old_rpath) < len(new_rpath):
            sys.exit("New rpath must not be longer than the old one.")
        self.bf.seek(rp_off)
        self.bf.write(new_rpath)
        self.bf.write(b'\0' * (len(old_rpath) - len(new_rpath) + 1))
        if len(new_rpath) == 0:
            self.remove_rpath_entry(entrynum)

    def remove_rpath_entry(self, entrynum):
        sec = self.find_section(b'.dynamic')
        if sec is None:
            return None
        for (i, entry) in enumerate(self.dynamic):
            if entry.d_tag == entrynum:
                rpentry = self.dynamic[i]
                rpentry.d_tag = 0
                self.dynamic = self.dynamic[:i] + self.dynamic[i + 1:] + [rpentry]
                break
        # DT_MIPS_RLD_MAP_REL is relative to the offset of the tag. Adjust it consequently.
        for entry in self.dynamic[i:]:
            if entry.d_tag == DT_MIPS_RLD_MAP_REL:
                entry.val += 2 * (self.ptrsize // 8)
                break
        self.bf.seek(sec.sh_offset)
        for entry in self.dynamic:
            entry.write(self.bf)
        return None

def run(args):
    if len(args) < 1 or len(args) > 2:
        print('This application resets target rpath.')
        print('Don\'t run this unless you know what you are doing.')
        print('%s: <binary file> <prefix>' % sys.argv[0])
        exit(1)
    with Elf(args[0]) as e:
        if len(args) == 1:
            e.print_rpath()
            e.print_runpath()
        else:
            new_rpath = args[1]
            e.fix_rpath(new_rpath)
    return 0

if __name__ == '__main__':
    run(sys.argv[1:])
