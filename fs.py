import os
import math
from structures import *

MAX_PARTITION_SIZE = 134217728
SECTOR_SIZE = 512
SECTORS_PER_BLOCK = 2

""" Dummy Fle System """
class DFS:
    PATH = 'dumb.bin'
    file = None
    partition_size = None

    def __init__(self):
        if not os.path.isfile(self.PATH):
            self.file = open(self.PATH, mode='wb')
            self.format(MAX_PARTITION_SIZE)
            self.file.close()
            self.file = open(self.PATH, mode='r+b')
        else:
            self.mount()

    def __exit__(self):
        self.unmount()

    def format(self, partition_size):
        self.file.seek(0, 0)
        
        blocks_count = ((partition_size // SECTOR_SIZE) // SECTORS_PER_BLOCK )

        superblock = Superblock.build(dict(magic=b"\x23\x23", blocks_count=blocks_count, free_blocks_count=blocks_count-1, first_free_block=1, first_data_block=1, block_size=Block.sizeof(), unused=b"\x00" * Superblock.unused.sizeof()))

        # Escreve bloco do superbloco
        self.file.write(superblock)
        self.file.write(b"\x00" * (Block.data.sizeof() - Superblock.sizeof()))
        self.file.write(b"\x5F" * Block.next.sizeof())

        # Escreve root
        #root = Block.build(dict(data=bytes(1020), next=0xFFFFFFFF))
        #self.file.write(root)

        # Escreve área de dados
        for ptr in range(1, blocks_count):
            block = Block.build(dict(data=bytes(992)+bytearray(28 * [0x5F]), next=(ptr+1)))
            self.file.write(block)
        
        self.file.seek(- Block.next.sizeof(), 1)
        self.file.write(b"\x5F" * Block.next.sizeof())

    def getSuperblock(self):
        self.file.seek(0, 0)
        return Superblock.parse(self.file.read(Superblock.sizeof()))

    def findFreeBlock(self):
        superblock = self.getSuperblock()
        if superblock.free_blocks_count > 0:
            return superblock.first_free_block
        else:
            print("$ No more space.")
    
    def mount(self):
        self.file = open(self.PATH, mode='r+b')

    def unmount(self):
        self.file.close()
        self.file = None

    def isMounted(self):
        return (self.file is not None)

    def lessThanOrEqual(self, x, y):
        if x <= y:
            return x
        else:
            return y

    def copyToFS(self, origin, destination):
        partition_size = os.path.getsize('dumb.bin')

        # Separar subdiretórios
        d = list(filter(lambda a: a != '', destination.split('/')))
        o = list(filter(lambda a: a != '', origin.split('/')))[-1]

        superblock = self.getSuperblock()
        how_many_blocks = math.ceil(os.path.getsize(origin) / superblock.block_size)

        self.file.seek(Block.sizeof())

        if(how_many_blocks < superblock.free_blocks_count):
            
            # Gravar o arquivo
            f = open(origin, mode="rb")

            for n in range(0, len(d)):
                verification = self.dirAlreadyExists(d[n]).block_location * Block.sizeof()
                if verification > 0:
                    self.file.seek(verification)
                else:
                    print("$ Informed file system path doesn't exist.")

            if str(self.dirAlreadyExists('').name) == '':
                self.file.seek(- Entry.sizeof(), 1)                  
                arq_size = os.path.getsize(origin)

                arq_entry = Entry.build(dict(name=o, attribute=0x20, block_location=superblock.first_free_block, size=arq_size))
                self.file.write(arq_entry)
                entry = Entry.parse(arq_entry)

                self.file.seek(entry.block_location * Block.sizeof())  # 33 * 1024 = 33792

                if arq_size < Block.data.sizeof():
                    self.file.write(f.read(arq_size))

                    self.file.seek(- arq_size, 1)
                    block = Block.parse(self.file.read(Block.sizeof()))
                    self.file.seek(- Block.next.sizeof(), 1)
                    self.file.write(b"\x5F" * Block.next.sizeof())

                    self.changeFreeBlock(block.next.to_bytes(Block.next.sizeof(), 'little'), superblock)
                
                else:
                    last_ptr = []

                    for i in range(0, os.path.getsize(origin), Block.data.sizeof()):
                        content = f.read(Block.data.sizeof())
                        self.file.write(content)
                        ptr = self.file.read(Block.next.sizeof())
                        self.file.seek(int.from_bytes(ptr, 'little') * Block.sizeof())

                        last_ptr.append(int.from_bytes(ptr, 'little') * Block.sizeof())

                        if last_ptr[-1] != 0:
                            self.file.seek(- Block.next.sizeof(), 1)
                            new_free_block = self.file.read(Block.next.sizeof())
                            self.changeFreeBlock(new_free_block, superblock)
                            self.file.seek((int.from_bytes(new_free_block, 'little') * Block.sizeof()))
                        
                    self.file.seek((last_ptr[-2] + Block.data.sizeof()))
                    last_free_block = self.file.read(Block.next.sizeof())
                    self.file.seek(- Block.next.sizeof(), 1)
                    self.file.write(b"\x5F" * Block.next.sizeof())
                    self.changeFreeBlock(last_free_block, superblock)
                    
            else:
                print("$ Block already used.")

            f.close()
        else:
            print("$ \nThere is not enough space.")

    def copyToHD(self, origin, destination, param):
        partition_size = os.path.getsize('dumb.bin')

        # Separar subdiretórios
        dirs = list(filter(lambda a: a != '', origin.split('/')))
        
        print(dirs)

        self.file.seek(self.getSuperblock().first_data_block * Block.sizeof())

        # Verificar se o diretório já existe no FS
        for n in range(0, len(dirs)):
            exist_entry = self.dirAlreadyExists(dirs[n])
            
            if exist_entry != False:
                print(f"$ Destination directory {dirs[n]} already exist!")
                self.file.seek(exist_entry.block_location * Block.sizeof())

                if exist_entry.attribute == b"\x20":
                    content = self.file.read(exist_entry.size).decode("utf-8")

                    dest = destination

                    if param == '-c':              # Cópia para o diretório atual
                        current_directory = os.getcwd()
                        dest = os.path.normpath(current_directory) + destination

                        if not os.path.exists(dest):
                            os.makedirs(dest)

                    elif param == '-d':            # Cópia para o desktop
                        desktop = os.path.normpath(os.path.expanduser("~/Desktop"))
                        dest = desktop + destination

                        if not os.path.exists(dest):
                            os.makedirs(dest)
                    
                    with open(dest + "/" + exist_entry.name, "w") as f:
                        f.write(content)
                
            else:
                print(f"$ Destination directory {dirs[n]} NOT exist!")
                break

    def getPartitionSize(self):
        return os.path.getsize(self.PATH)

    def dirAlreadyExists(self, dir_name):
        for entry in range(0, int(self.getPartitionSize()/Entry.sizeof()), Entry.sizeof()):
            entry = Entry.parse(self.file.read(Entry.sizeof()))
            entry_name = ''.join(list(filter(lambda a: a != '', entry.name.split('\x00'))))
            
            if entry_name == dir_name:
                return entry
            else:
                if entry_name == '':
                    return False

                if entry_name[0] == "\x5F":
                    return True

    def changeFreeBlock(self, free_block, superblock):
        # Atualiza free_blocks_count
        self.file.seek(6)
        self.file.write((superblock.free_blocks_count - 1).to_bytes(4, byteorder='little'))

        # Atualiza first_free_blocks
        self.file.seek(10)
        self.file.write(free_block)

    def mkdir(self, path):
        dirs = list(filter(lambda a: a != '', path.split('/')))
        
        superblock = self.getSuperblock()
        parent = Entry.parse(Entry.build(dict(name="", attribute=0x10, block_location=superblock.first_free_block, size=0)))

        self.file.seek(superblock.first_data_block * Block.sizeof())

        # For para cada diretório
        for n in range(0, len(dirs)):
            
            if len(dirs) == 1:
                parent = self.dirAlreadyExists(dirs[n])
                if parent == False:
                    entry_pos = self.file.tell()

                    # Fazer ficar sempre no começo do bloco
                    self.file.seek(- (entry_pos - (Block.sizeof() * superblock.first_data_block)), 1)
                    block = Block.parse(self.file.read(Block.sizeof()))

                    self.file.seek((entry_pos - Entry.sizeof()))

                    entry = Entry.build(dict(name=dirs[n], attribute=b"\x10", block_location=block.next, size=0))
                    self.file.write(entry)

                    self.file.seek(((int(hex(block.next), 16) * Block.sizeof()) + Block.data.sizeof()))
                    new_free_block = self.file.read(Block.next.sizeof())
                    self.file.seek(- Block.next.sizeof(), 1)
                    self.file.write(b"\x5F" * Block.next.sizeof())
                    
                    self.changeFreeBlock(new_free_block, superblock)
                    self.file.seek(entry_pos)
                    self.file.seek(((Block.sizeof()*superblock.first_data_block) - (entry_pos - Block.sizeof()) - Block.next.sizeof()), 1)
                    self.file.write(new_free_block)

                    self.file.seek(entry_pos)

                elif parent == True:
                    #self.file.seek(- Block.next.sizeof(), 1)
                    #self.file.write(b"\x5F" * Block.next.sizeof())
                    
                    self.file.seek((superblock.first_free_block * Block.sizeof()))   # Vai para a posição 21
                    entry_pos = self.file.tell()                                     # 33792

                    block = Block.parse(self.file.read(Block.sizeof()))
                    self.file.seek(- Block.sizeof(), 1)

                    entry = Entry.build(dict(name=dirs[n], attribute=b"\x10", block_location=block.next, size=0))
                    self.file.write(entry)

                    self.file.seek(((block.next * Block.sizeof()) + Block.data.sizeof()))
                    new_free_block = self.file.read(Block.next.sizeof())
                    self.file.seek(- Block.next.sizeof(), 1)
                    self.file.write(b"\x5F" * Block.next.sizeof())
                    
                    self.file.seek((entry_pos + Block.data.sizeof()))
                    self.file.write(new_free_block)

                    self.file.seek(14)
                    self.file.write(superblock.first_free_block.to_bytes(Block.next.sizeof(), 'little'))

                    self.file.seek(entry_pos)
            else:
                parent = self.dirAlreadyExists(dirs[n])
                
                if parent == False:
                    entry_pos = self.file.tell()

                    # Fazer ficar sempre no começo do bloco
                    self.file.seek(- (entry_pos - (Block.sizeof() * superblock.first_data_block)), 1)
                    block = Block.parse(self.file.read(Block.sizeof()))

                    self.file.seek((entry_pos - Entry.sizeof()))

                    entry = Entry.build(dict(name=dirs[n], attribute=b"\x10", block_location=block.next, size=0))
                    self.file.write(entry)

                    self.file.seek(((int(hex(block.next), 16) * Block.sizeof()) + Block.data.sizeof()))
                    new_free_block = self.file.read(Block.next.sizeof())
                    self.file.seek(- Block.next.sizeof(), 1)
                    self.file.write(b"\x5F" * Block.next.sizeof())
                    
                    self.changeFreeBlock(new_free_block, superblock)
                    self.file.seek(entry_pos)
                    self.file.seek(((Block.sizeof()*superblock.first_data_block) - (entry_pos - Block.sizeof()) - Block.next.sizeof()), 1)
                    self.file.write(new_free_block)

                    self.file.seek(entry_pos)
                else:
                    self.file.seek(parent.block_location * Block.sizeof())

    def ls(self):
        self.file.seek(1 * Block.sizeof())
        level = 0
        last_dir = []

        for e in range(0, int(self.getPartitionSize()/Entry.sizeof()), Entry.sizeof()):
            entry = Entry.parse(self.file.read(Entry.sizeof()))
            entry_name = ''.join(list(filter(lambda a: a != '', entry.name.split('\x00'))))

            if entry.block_location != 0:
                if entry.attribute == b'\x10':
                    print(self.tabSpaces(level) + '/' + entry_name)

                    level = level + 1
                    last_dir.append(self.file.tell())
                    
                    self.file.seek(entry.block_location * Block.sizeof())

                elif entry.attribute == b'\x5F':
                    if entry.size != b'\x5F':
                        self.file.seek(entry.size * Block.sizeof())
                    else:
                        break
                else:
                    print(self.tabSpaces(level) + entry_name)
            else:    
                level = level - 1
                
                if level < 0:
                    break
                
                self.file.seek( last_dir[-level] )
                last_dir.pop()

    def tabSpaces(self, how_many_tabs):
        return ((lambda x: how_many_tabs * x)('\t'))
