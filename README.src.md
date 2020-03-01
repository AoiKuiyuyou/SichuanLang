[:var_set('', """
# Compile command
aoikdyndocdsl -s README.src.md -g README.md
""")]\
[:HDLR('heading', 'heading')]\
# SichuanLang
四川话编程语言。基于Python 3.5+，可与Python模块互相引入。

请看[示例](/src/sichuanlang/demo)和[语法](/syntax.md)。


## 内容
[:toc(beg='next', indent=-1)]


## 安装
[:tod()]


### 用pip
运行：
```
pip install SichuanLang
```
或运行：
```
pip install git+https://github.com/AoiKuiyuyou/SichuanLang
```


### 用python
运行：
```
wget https://github.com/AoiKuiyuyou/SichuanLang/archive/master.zip

unzip master.zip

cd master

python setup.py install
```


## 用法


### 启动程序
安装后运行：
```
sichuanlang
```
或安装后运行：
```
python -m sichuanlang
```
或不安装直接运行：
```
python SichuanLang/src/sichuanlang/__main__.py
```

### 运行四川话模块
四川话模块文件以`.sichuan`扩展名结尾。

运行：
```
sichuanlang -m 四川话模块名或文件路径
```

模块名无需后加`.sichuan`扩展名。
模块文件路径需后加`.sichuan`扩展名。


### 把四川话模块转换成Python源码
运行：
```
sichuanlang -m 四川话模块名或文件路径 -p > 输出文件.py
```


### 在Python源码中引入四川话模块
在Python源码中先引入`sichuanlang.enable_import`模块，之后就可像引入Python模块一样引入四川话模块。例如：
```
import sichuanlang.enable_import
import some.sichuanlang.module
```
这里有个[例子](/src/sichuanlang/demo/test.py)。


## 示例
请看[示例](/src/sichuanlang/demo)。


## 语法
请看[语法](/syntax.md)。
