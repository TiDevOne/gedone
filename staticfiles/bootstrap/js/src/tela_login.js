// Get the modal
var modal = document.getElementById("myModal");

// Get the link that opens the modal
var link = document.getElementById("forgot-password");

// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close")[0];

// When the user clicks on the link, open the modal
link.onclick = function() {
  modal.style.display = "block";
}

// When the user clicks on <span> (x), close the modal
span.onclick = function() {
  modal.style.display = "none";
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
  if (event.target == modal) {
    modal.style.display = "none";
  }
}

// Function to handle form submission
document.getElementById("submit").onclick = function() {
  var cpf = document.getElementById("cpf").value;
  var email = document.getElementById("email").value;
  // Do something with the entered data, like sending it to the server for password recovery
  console.log("CPF:", cpf);
  console.log("Email:", email);
  // Close the modal
  modal.style.display = "none";
}

