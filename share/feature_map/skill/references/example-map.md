# A worked feature map

One real map, and why every line is there. Copy the shape, not the paths.

`.features/signup.yaml`:

```yaml
feature_name: signup
purpose: "How a new account is created and reaches the first authenticated screen."

entry_points:
  - api/src/signup/handler.go
  - web/src/routes/signup/+page.svelte
  - api/src/jobs/welcome_email.go

apps:
  - api
  - web

user_flow:
  primary: "Visitor submits email → API creates user + session → redirect to /app"
  error: "Duplicate email → 409 → form shows sign-in link"

related_features:
  - billing (free plan attached on first login)
  - auth (session issued here, refreshed there)

notes: >
  Confirm the Stripe webhook path before changing plan assignment.
```

## Why each line

- `feature_name` matches the filename stem (`signup.yaml`). `validate` warns otherwise.
- `purpose` is one sentence and names the **span** — where the feature starts and
  where it ends. That is what tells the next agent whether this is the right map.
- `entry_points` are **doors**: the HTTP handler, the page a user lands on, the job
  that fires after. Not every file signup touches — no models, no helpers, no tests.
  Three real paths beat twelve invented ones; `check` verifies they exist on disk.
- `apps` lists names, not descriptions. `check` uses them as path prefixes, and
  `stats` uses them to tell you which app has no map yet.
- `user_flow.primary` is one line, `Actor → step → result`. `error` is there only
  because the code genuinely branches; drop it when it does not.
- `related_features` entries start with a **resolvable slug**, then a parenthetical
  saying what the coupling *is*. `graph` reads the slug; a human reads the phrase.
- `notes` holds one unknown. No history, no changelog, no process tips. If there is
  nothing to warn about, omit the key entirely.

## The same feature, done wrong

```yaml
feature_name: signup_flow          # does not match signup.yaml
purpose: >                         # three paragraphs of motivation
  Signup is one of the most important parts of the product, because acquisition
  drives everything downstream, and historically we have struggled with ...
entry_points:
  - api/src/signup/handler.go
  - api/src/signup/validator.go    # not a door
  - api/src/models/user.go         # not a door
  - web/src/lib/forms/Input.svelte # not a door
architecture: "The API is a Go monolith ..."   # narrative key; not in the schema
related_features:
  - "we also touch billing somewhere"          # no resolvable slug
```

Every problem above is mechanical: `validate` catches the name mismatch and the
unresolvable link, `check` stays quiet while the file list quietly rots, and a
reader still cannot tell which file to open. Density is the point — see
`authoring.md`.
