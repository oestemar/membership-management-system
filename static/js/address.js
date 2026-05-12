document.addEventListener("DOMContentLoaded", function () {

    const searchBtn = document.getElementById("searchAddress");
    if (!searchBtn) return;  // ボタンがない画面では何もしない

    searchBtn.addEventListener("click", function () {

        const zip1 = document.getElementById("zip1").value;
        const zip2 = document.getElementById("zip2").value;
        const zipcode = zip1 + zip2;
        document.getElementById("zipcode").value = zipcode;

        if (zipcode.length !== 7) {
            alert("郵便番号は7桁で入力してください");
            return;
        }

        const url = "https://zipcloud.ibsnet.co.jp/api/search?zipcode=" + zipcode;

        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data.results) {
                    const result = data.results[0];
                    const addr = document.getElementById("address");

                    if (addr) addr.value = result.address1 + result.address2 + result.address3;

                } else {
                    alert("住所が見つかりませんでした");
                }
            })
            .catch(error => {
                console.error("Error:", error);
                alert("住所検索に失敗しました");
            });
    });
});
