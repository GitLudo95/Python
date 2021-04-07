const validateForm = () => {
	const forms = document.querySelectorAll('.needs-validation')
  	Array.prototype.slice.call(forms).forEach((form) => {
      form.addEventListener('submit', function (event) {
      	document.getElementById("loadingSpinner").style.display = "block";
        if (!form.checkValidity()) {
          event.preventDefault()
          event.stopPropagation()
        }

        form.classList.add('was-validated')
      }, false)
    })
}

window.onload = function() {
	console.log("Hello world");
	document.getElementById("loadingSpinner").style.display = "none";
	if(!!ticker) {
		console.log("ticker:" + ticker);
		expandCard("StockInfoCollapse");
	}
	if(!!errorMessage) {
		document.getElementById("StockInfoAlertDanger").style.display = "block";
	}
	if(!!financialInfo) {
		document.getElementById("StockInfoAlertInfo").style.display = "block";
	}
	validateForm();
}

const parseTicker = (e) => {
	const ticker = e.target.value;
	if(ticker && ticker.includes(" - ")) {
		document.getElementById("StockTicker").value = ticker.split(" ")[0];
	}
}

const collapseCard = (id) => {
	const card = document.getElementById(id);
	card.classList.remove("show");
}

const expandCard = (id) => {
	const card = document.getElementById(id);
	card.classList.add("show");
}