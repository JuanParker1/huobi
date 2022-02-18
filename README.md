# Git 使用指南
## 1. 一些常用操作
### 1.1	添加和删除（暂存区）
- 初始化文件夹\
    git init

- 添加修改后文件/新建文件 到暂存区\
    git add <file>

- 添加所有文件\
    git add .

- 删除指定的暂存文件（本地仓库和远程仓库都会删除，但本地文件不会删除）\
    git rm --cached <file>
    或
    git rm -r --cached <file>
    > 删除单个文件不用加上（-r），删除文件夹需要（-r），即递归删除该文件夹。

- 仓库 和 本地文件都删除\
    git rm <file>

### 1.2	提交和撤回
- 将暂存文件提交，其中"description" 是提交描述\
    git commit -m "description"

- 撤回，退回到以提交过的任意版本：\
    git reset --hard <xxx>
    > 其中<xxx>为某次提交的哈希值，可以使用git log或git reflog查看

### 1.3	远程仓库
- 添加远程仓库\
    git remote add <origin> <addr>
    > 添加远程仓库, 默认的就是origin, addr就是仓库地址,比如输入：\
    git remote add origin git@github.com:<>/<>.git

- 获取远程仓库名\
    git remote

- 查看远程分支url\
    git remote -v

- 转换远程分支url（eg.从http到ssh）\
    git remote set-url origin git@github.com:<用户名>/<仓库名>.git

- 将本地仓库同步到远程仓库\
    git push -u <origin master>\
    同步的时候需要注意几点：
    - 第一、需要将远端的地址记录在本地\
    git remote add origin 仓库地址（直接在github仓库网页的地址栏复制即可）
    - 第二、第一次提交远端时，远端会认为这是无关的仓库，所以需要先关联一下\
    git pull origin master --allow-unrelated-histories
    - 第三、当本地版本落后于远端时，需要先pull一下\
    git pull origin master


- 拉取远程仓库\
    git pull <origin master>

- 拉取远程仓库的某个分支，并与本地某分支合并：\
    git pull <远程主机名> <远程分支名>:<本地分支名>

- 克隆项目\
    git clone url

### 1.4	分支
- 新建分支\
    git branch <分支名>

- 删除本地分支\
    git branch -d <分支名> //删除本地分支

- 切换到某分支\
    git checkout <分支名>

- 查看所有分支名\
    git branch -a

- 查看远程分支名\
    git branch -r

- 修改分支名\
    git branch -m <旧分支名> <新分支名>

### 1.5	查看分支状态、日志
- 查看当前分支中的文件状态\
    git status

- 提交完成之后，查看提交日志\
    git log
    或
    git reflog
    > 这两个命令的输出中都有一个HEAD，它是一个指针，指向当前分支中的某个提交

### 1.6	查看、修改文件内容
- 查看文件内容\
    cat <file>

- 修改文件内容\
    vim <file>
    > 修改完后按 esc 键退出编辑模式后，输入”:wq”，保存修改并退出


## 2. 常见报错
### 2.1	error: failed to push some refs to '.......'
错误原因1：远程仓库和本地库不一致
解决:
1. 取消刚才的commit（提交）并同步远程的仓库\
    git pull --rebase <origin master>

    git push
    或者
    git push -u <origin master>\
    其中<>中为远程仓库名

2. 合并本地和远程仓库，并同步远程仓库
    git merge <origin master>\
    git push -u <origin master>

### 2.2 unable to access ‘https://github.com/…/’: OpenSSL SSL_read: Connection was reset, errno 10054

原因1：一般是因为服务器的SSL证书没有经过第三方机构的签署，所以才报错。

解决办法：解除SSL验证\
git config --global http.sslVerify false\
再次 git push 即可


### 2.3 使用git时将部分文件写入.gitignore依旧上传的问题

本地有缓存，需要清理掉

执行前记得先把所有需要的东西先push到git，否则可能被删除

git rm -r --cached .
 
git add .
 
git commit -m 'update .gitignore'

# Markdown
官方文档
创始人的markdown语法说明
https://daringfireball.net/projects/markdown/syntax

## 1.一些常用操作
### 1.1	标题
在文本前面加上 # 即可，总共六级标题，标题字号相应降低。
# 一级标题
## 二级标题
### 三级标题
#### 四级标题
##### 五级标题
###### 六级标题 

### 1.2	列表格式
无序列表
在文字前加上 - 或 * 或 + 即可
- 文本1
- 文本2
- 文本3

有序列表
在文字前加：数字序号.<space>文本
1. 文本1
2. 文本2
3. 文本3

列表嵌套
上一级和下一级之间敲三个空格即可
- 一级无序列表内容
- 二级无序列表内容
- 二级无序列表内容
- 二级无序列表内容


### 1.3	引用
在你希望引用的文字前面加上 >，注意 > 和文本之间要保留一个字符的空格。

> 一盏灯， 一片昏黄； 一简书， 一杯淡茶。

### 1.4	粗体和斜体

用两个 * 包含一段文本就是粗体的语法，用一个 * 包含一段文本就是斜体的语法。要倾斜和加粗的文字左右分别用三个*号包起来。用两个~~号包起来是加删除线的语法。例如：

 *这是斜体*，**这是粗体**，***这是加粗的斜体***，~~这是加删除线的文字~~，这是平常字体。

### 1.5	代码引用
如果引用的语句只有一段，不分行，可以用 ` 将语句包起来。
如果引用的语句为多行，可以将```置于这段代码的首行和末行。


```c++
int a[3][4] = { 0,1,2,3,4,5,6,7,8,9,10,11 };
int(*p)[4];
p = a;
std::cout << (*p)[0] << ' ' << (*p)[1] << ' ' << (*p)[2] << ' ' << (*p)[3] << ' '<< std::endl;
std::cout << *p[0] << ' ' << *p[1] << ' ' << *p[2] << ' ' << std::endl;
```

### 1.6	表格

语法：\
表头|表头|表头
---|:--:|---:
内容|内容|内容
内容|内容|内容

第二行分割表头和内容。
- 有一个就行，为了对齐，多加了几个
文字默认居左
- 两边加：表示文字居中
- 右边加：表示文字居右
注：原生的语法两边都要用 | 包起来。此处省略


示例代码：

| Tables        | Are           | Cool  |
| ------------- |:-------------:| -----:|
| col 3 is      | right-aligned | $1600 |
| col 2 is      | centered      |   $12 |
| zebra stripes | are neat      |    $1 |



### 1.7	流程图

```flow
st=>start: 开始
op=>operation: My Operation
cond=>condition: Yes or No?
e=>end
st->op->cond
cond(yes)->e
cond(no)->op
&```
