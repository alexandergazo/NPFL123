### Chosen Domain: Twitter

### Intens
- greet
- goodbye
- find_tweet
- show_themes
- show_theme_keywords
- show_user_categories
- show_users_in_category
- add_user_to_category
- remove_user_from_category
- add_user_category
- remove_user_category
- add_keyword_to_theme
- remove_keyword_from_theme
- add_theme
- remove_theme
- show_tweet
- swow_tweeting_themes_of_user
- show_keyword_frequency_in_user_category
- search_user

### Slots - Values

- user - any valid twitter @
- keyword - any string
- theme - any word
- user_category - any string
- time_range - {this year, last year, last month, this month, ...}
- pick_metric - {most RT, most likes, most recent}
- query - any string

### Examples

The last three examples in `examples.tsv` assume that there exists a context with time_range and tweet set specified preceding the utterance.

