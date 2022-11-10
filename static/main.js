if (document.querySelector("#go-back")) this.addEventListener("click", () => window.history.back());

const btns = document.querySelectorAll(".fa-eye-slash");
for (let i = 0; i < btns.length; i++) btns[i].addEventListener("click", () => {
    const pass = btns[i].previousElementSibling;
    const type = pass.getAttribute("type") === "password" ? "text" : "password";
    pass.setAttribute("type", type);
    btns[i].classList.toggle("fa-eye")
    btns[i].classList.toggle("fa-eye-slash")
});
