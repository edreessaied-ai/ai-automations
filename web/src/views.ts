/*
  This file contains functions to manage the visibility of different sections of the UI.
*/


export function hideAll() {
  /* 
    Hide all sections of the UI. 

    This is typically called before showing a specific section to
    ensure only one section is visible at a time.
  */
  document.querySelectorAll("section").forEach((s) => {
    s.classList.add("hidden");
  });
}


export function showLanding() {
  /*
    Show the landing page section and hide all others.
  */
  hideAll();
  document.getElementById("landing-state")?.classList.remove("hidden");
}


export function showForm() {
  /*
    Show the form section and hide all others.
  */
  hideAll();
  document.getElementById("form-state")?.classList.remove("hidden");
}


export function showSlack() {
  /*
    Show the Slack integration section and hide all others.
  */
  hideAll();
  document.getElementById("slack-state")?.classList.remove("hidden");
}


export function showAPI(): void {
  /*
    Show the API documentation section and hide all others.
  */
  hideAll();
  document.getElementById("api-state")?.classList.remove("hidden");
}


export function showUnknown() {
  hideAll();
  document.getElementById("unknown-state")?.classList.remove("hidden");
}


export function showSubmitted(): void {
  hideAll();

  const section = document.getElementById("state-submitted");
  if (!section) {
    console.warn("showSubmitted: section not found");
    return;
  }

  section.classList.remove("hidden");
}