from fs import DFS
import shlex
import os

def main():
    print("\nShell")
    print("***** Welcome to DummyFS *****\n")
    fs = DFS()

    while True:
        command = shlex.split(input('$ '))
        print(f"ECHO: {command}")
        
        if len(command) == 1:   # Comando sem parâmetros
            if command[0] == 'exit':
                print("\nExiting...")
                exit(0)
            elif command[0] == 'help':
                print("----------------------------------------------------")
                print("DUMMYFS\n")
                print("ls - list directory and files")
                print("format - format to max size defined")
                print("mkdir - create directory")
                print("copy2fs - copy file from disk to the file system")
                print("copy2hd - copy file from the file system to the disk")
                print("checkname - verify name inconsistency")
                print("del - delete file from the filesystem\n")
                print("----------------------------------------------------")
            elif command[0] == 'ls':
                fs.ls()
            elif command[0] == 'clear':
                clear()
            elif command[0] == 'format':
                partition_size = 134217728
                #partition_size = 4294967296
                fs.format(partition_size)

            elif command[0] == 'checkname':
                fs.checkname()
            else:
                print("Unknown command.")

        elif len(command) == 2:
            if command[0] == 'format':
                # Tamanho máximo da partição = 134217728 bytes = 128 MiB
                # 134217728 bytes / 512 bytes = 262144 setores
                # 262144 setores / 2 setores_por_bloco => 131072 blocos

                partition_size = int(command[1])

                if partition_size <= MAX_PARTITION_SIZE and partition_size >= SECTOR_SIZE and partition_size % SECTOR_SIZE == 0:
                    fs.format(partition_size)
                else:
                    print("$ Exceeded partition size or it's not multiple of 512. \nMinimum size = 512.\nMaximum size = 134217728.")
            
            elif command[0] == 'mkdir':
                fs.mkdir(command[1])
            
            elif command[0] == 'del':
                fs.delete(command[1])
            else:
                print("Unknown command.")
        
        elif len(command) == 3:
            if command[0] == 'copy2fs':
                origin = command[1]
                destination = command[2]
                fs.copyToFS(origin, destination)

            elif command[0] == 'copy2hd':
                origin = command[1]
                destination = command[2]
                fs.copyToHD(origin, destination, 0)

            else:
                print("Unknown command.")

        elif len(command) == 4:
            if command[0] == 'copy2hd':
                origin = command[1]
                destination = command[2]
                fs.copyToHD(origin, destination, command[3])
            else:
                print("Unknown command.")

if __name__ == '__main__':
    main()