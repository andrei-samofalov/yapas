function increaseCounter() {
  const counter = document.getElementById('counter')
  let current = parseInt(counter.innerHTML)
  if (!current) {
    counter.innerHTML = "1"
  } else {
    current += 1
    counter.innerHTML = String(current)
  }
}
