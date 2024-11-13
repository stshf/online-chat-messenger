# online chat messenger
本プロジェクトは、簡単なソケット通信を通して異なるプログラミング言語間でJSONをやり取りする

# 仕様
Client: Python
Server: Javascript(Node.js)

# Client Side
- json
    - `dict.dump() -> json.encode() -> json_binary`
    - `json_binary.decode() -> json.load() -> dict`

# Server Side
- node.js
- nvm
    - node version manager
- npm
    - node package manager

- [WSL2へのnode.jsのインストール](https://learn.microsoft.com/ja-jp/windows/dev-environment/javascript/nodejs-on-wsl)
    - curlのインストール
        ```bash
        sudo apt-get install curl
        ```
    - curlを使用したnvmのインストール
        ```bash
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/master/install.sh | bash
        ```
    - インストールの確認
        ```bash
        command -v nvm
        ```
        `nvm`とかえってこればOK
    - 現在インストールされているNodeのバージョンを一覧表示
        ```bash
        nvm ls
        ```
        ```
            N/A
        iojs -> N/A (default)
        node -> stable (-> N/A) (default)
        unstable -> N/A (default)
        ```
    - 現在のバージョンと安定バージョンの両方のNode.jsをインストール
        - 安定したLTSリリースをインストール
            ```bash
            nvm install --lts
            ```
        - 最新のリリースをインストール
            ```bash
            nvm install node
            ```
    - インストールされているversionを一覧表示:`nvm ls`
    - プロジェクトに使用するNode.jsのバージョンを変更する
        - プロジェクトディレクトリに移動: `cd project-dir`
        - Node.jsのバージョンを変更
            - 最新バージョン: `nvm use node`
            - 安定バージョン: `nvm use --lts`
    - 動作確認
        - sample fileの作成 [引用](https://nodejs.org/api/synopsis.html)
            hello-world.js
            ```node.js
            const http = require('node:http');

            const hostname = '127.0.0.1';
            const port = 3000;

            const server = http.createServer((req, res) => {
            res.statusCode = 200;
            res.setHeader('Content-Type', 'text/plain');
            res.end('Hello, World!\n');
            });

            server.listen(port, hostname, () => {
            console.log(`Server running at http://${hostname}:${port}/`);
            });
            ```
        - 実行: `node hello-world.js`
            result
            ブラウザ上で`127.0.0.1:3000` or `http://localhost:3000`を入力し、`Hello, World!`が表示されたらOK
