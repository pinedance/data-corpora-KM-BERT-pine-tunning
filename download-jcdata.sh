curl --insecure --proxy "socks5h://127.0.0.1:8844" -O https://gitlab.com/jicheng/jc.data/-/archive/master/jc.data-master.tar.gz
# curl --insecure -O https://gitlab.com/jicheng/jc.data/-/archive/master/jc.data-master.tar.gz

tar -xzf jc.data-master.tar.gz
mkdir -p rawdata
cp -r jc.data-master/pages/book rawdata/

rm -rf jc.data-master
rm -rf jc.data-master.tar.gz
# rm -rf rawdata
# rm -rf data

# for F in rawdata/book/**/*.html; do echo $F; done

mkdir -p export
cat rawdata/book/**/*.html > rawdata/books.html