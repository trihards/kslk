# KSLK

Slacker Chill radio: a homemade Spotify playlist series on a tuner dial. Turn the dial, pull a tape, play it.

Live at **https://trihards.github.io/kslk/**

## What's on the station

Nine mood shelves, ordered on the dial from mellower to louder: Gentle – Quiet, Golden, Beeps and Boops, Funk This Day, Hippity Hoppity, Feelin' Fine, Rump Shakin', Rock the Fock On, and Yee Haw. Volumes over 50 tracks live in the crate zone instead.

The page also has Tape of the Day (one pick per day, same for everyone), Spin the dial (random from everything), Pick one for me (random from the current shelf), search across song titles, artists, and volume names, a shelf/wall toggle for cover art, and a Spotify player deck that keeps playing while you browse.

## How the sorting works

Each volume's mood was drafted by clustering its Spotify audio features (energy, valence, danceability, acousticness, instrumentalness, speechiness) together with its artists' genres, then named and corrected by hand. A stripe on a tape means it sits close to a second mood and appears on both shelves. Two overrides keep genre honest: volumes that are mostly reggae or afro go to Feelin' Fine, and mostly-country volumes go to Yee Haw.

Vol 00 (Freakshow on the Dance Flo') is pinned to the top of Funk This Day and exempt from the crate cutoff. Otherwise, shelves list main-mood volumes first, then second-mood ones, highest volume number first. "Newest" marks the three most recently started volumes. Cover art and liner notes come straight from each playlist's Spotify image and description.

## Refreshing

1. Export all playlists with [Exportify](https://exportify.app), with the audio features box ticked.
2. Run `tools/get_playlist_ids.py` to get `playlist_ids.csv`.
3. Run `tools/get_slacker_covers.py` to get `slacker_covers.zip` (covers and descriptions).
4. Hand the current `index.html` plus those three files to Claude to rebuild. All the page's data is embedded in `index.html`, so it doubles as the source.
5. Upload the new `index.html` here. The footer's "Last updated" date changes with each rebuild.

The scripts need a Spotify developer app (Premium has been required to create one since February 2026) with the redirect URI `http://127.0.0.1:8888/callback`. They ask for the Client ID when they run. Never commit a Client ID, a token, or the raw Exportify CSVs, which include your Spotify username and when every track was added.

## Notes

The page is one self-contained file of about 3.3 MB, with covers embedded as 300-pixel images. The player is Spotify's embed: logged-out listeners get 30-second previews, and iPhone Safari often sticks to previews even when logged in. Open in Spotify always gets the full playlist.

## Changelog

- **2026-10-01:** Cover art and liner notes, wall view, Spotify player deck, Vol 00 pinned to Funk This Day, collapsible search, Tape of the Day.
- **2026-09-30:** First broadcast: nine mood shelves, crate zone, color key, search, Spin the dial, Newest tags.
