const express = require("express");
const app = express();

app.use(express.json());

app.post("/webhook", (req, res) => {
  console.log(req.body);
  res.send("OK");
});

app.get("/", (req, res) => {
  res.send("Webhook app is running");
});

const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log("Server running on port " + port);
});
