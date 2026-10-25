# Spain branch modifiers and events

Spanish Air Force is added by **Reorganise the Air Command** (A01), and Spanish
Navy by **Establish the Naval Staff** (N01). Both first-focus rewards display the
modifier in their native tooltips. Choosing Volunteer or War Spain now adds only
Spanish Economy and Spanish Armed Forces. Air and navy rewards keep their values.

The daily refresh handles existing saves: premature air/navy modifiers disappear
until their first focus is earned. Completed focuses or their reward flags restore
the appropriate modifier without clearing accumulated bonuses or paying twice.

The script regression suite executes the request to Germany, both replies and the
retry decision, preserving recipient/sender scopes and the one-day event delays.
Acceptance now rechecks current diplomatic eligibility, including a request that
expired while its event panel was open. A changed faction, subject status, war,
German government or faction leadership cannot force an invalid admission.
Pending requests cannot be queued repeatedly.

Portuguese relocation completion now requires an active, unfinished relocation,
so repeated calls cannot send the completion notification again. Its test delays
dockyard transfer until a valid coastal destination exists, clears event targets
to simulate a new daily context, completes the transfer and delivers one notice.
Both Labour Accords options are executed: each pays its political effects once
and leaves the recovery programme intact. All five custom events, their options
and localisation references are covered.

The user's existing Workshop edits are preserved: War Spain and Domestic Chemical
Industry positions, plus Equipment Shipments at cost 5 with 2,000 infantry
equipment. The plan and structural baselines record these edits explicitly.

Validation: 98 repository tests passed, including seven new branch/event tests;
generation is reproducible. These are script-level tests, not proof of every event
in a live campaign. Close the game before copying the changed focus file into
Workshop: reloading it during play previously left invalid native focus pointers.
