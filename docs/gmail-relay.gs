// Gmail relay for Nexus ATS password-reset e-mails (free: about 100 e-mails a day, sent from the script owner's Gmail).
// Setup: script.google.com -> New project -> paste this -> change SECRET -> Deploy -> New deployment -> type "Web app"
//   -> Execute as: Me, Who has access: Anyone -> Deploy -> authorise -> copy the "Web app" URL.
// In Render set MAIL_RELAY_URL = that URL and MAIL_RELAY_SECRET = the same SECRET.
var SECRET = "CHANGE-ME-to-a-long-random-text";

function doPost(e) {
  var out = ContentService.createTextOutput().setMimeType(ContentService.MimeType.JSON);
  try {
    var d = JSON.parse(e.postData.contents);
    if (SECRET === "CHANGE-ME-to-a-long-random-text" || d.secret !== SECRET) return out.setContent('{"ok":false}');
    MailApp.sendEmail({ to: d.to, subject: d.subject, body: d.text, name: "Nexus ATS" });
    return out.setContent('{"ok":true}');
  } catch (err) {
    return out.setContent('{"ok":false}');
  }
}
