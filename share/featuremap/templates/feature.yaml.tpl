feature_name: {{feature_name}}
purpose: "Describe what {{FEATURE_TITLE}} does and why it matters."

entry_points:
  - path/to/primary/entry_point
  - path/to/secondary/surface

apps:
  - app_name

user_flow:
  primary: "Describe the main user journey."

related_features:
  - related_feature_slug (brief note)

notes: >
  Authoring tips: keep entry_points as real file paths where possible.
  Run `featuremap validate` and `featuremap check` after edits.
