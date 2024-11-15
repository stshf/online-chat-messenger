
// floor(double x): 10 進数 x を最も近い整数に切り捨て、その結果を整数で返す。
let floor = ((x) => {
    return Math.floor(x);
})

// nroot(int n, int x): 方程式 rn = x における、r の値を計算する。
let nroot = ((n, x) => {
    return Math.pow(x, 1 / n);
})

// reverse(string s): 文字列 s を入力として受け取り、入力文字列の逆である新しい文字列を返す。
let reverse = ((s) => {
    return s.split("").reverse().join("");
})


// validAnagram(string str1, string str2): 2 つの文字列を入力として受け取り，2 つの入力文字列が互いにアナグラムであるかどうかを示すブール値を返す。
let validAnagram = ((s1, s2) => {
    return s1.split("").sort().join("") === s2.split("").sort().join("");
})

// sort(string[] strArr): 文字列の配列を入力として受け取り、その配列をソートして、ソート後の文字列の配列を返す。
let sort = ((strArr) => {
    return strArr.sort();
})

let hashMap = {
    "floor": floor,
    "nroot": nroot,
    "reverse": reverse,
    "validAnagram": validAnagram,
    "sort": sort,
}

