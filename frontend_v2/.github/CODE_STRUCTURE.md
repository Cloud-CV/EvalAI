# CODE STRUCTURE

## Directory structure

The URL structure of the project can be found [below](#url structure).
The directory structure of `src/` looks like this:

```
.
├── app
│   ├── components
│   └── services
├── assets
│   ├── fonts
│   └── images
│       ├── get_involved
│       ├── partners
│       ├── rules
│       └── testimonials
├── environments
└── styles
``` 
It can be seen that the top level directories in the `src` folder are:
- `app` - This contains the main app component and houses all the components and services
	- `components` - Contains all the components (Views for all pages & Reusable components). See [section](#components) below. 
	- `services` - Contains all the injectable services that contain common functionalities.
		- _auth.service.ts_ - Authentication functions
		- _api.service.ts_ - Api call functions
		- _challenge.service.ts_ - Challenge related functions
		- _global.service.ts_ - Global common functionality
		- _window.service.ts_ - DOM specific functions
- `assets` - Contains static assets like fonts, images etc.
- `environments` - Contains API paths for `dev`, `staging` and `prod` environments.
- `styles` - Contains common style files which can be imported in the components.
	- _mixins.scss_ - Contains reusable mixins for screen sizes, box-shadow, gradients and keyframes.
	- _variables.scss_ - Contains color codes, screen sizes and font-weights .
	- _base.scss_ - Contains styles for buttons, tables, cards, modals, stylish-checkbox etc.

### Components

The directory structure of the components is as below.

```
.
├── about
├── auth
│   ├── login
│   ├── signup
│   └── verify-email
├── challenge
│   ├── challengeevaluation
│   ├── challengeleaderboard
│   ├── challengeoverview
│   ├── challengeparticipate
│   ├── challengephases
│   │   └── phasecard
│   ├── challengesubmissions
│   └── challengesubmit
├── challenge-create
├── contact
├── dashboard
├── get-involved
├── home
│   ├── featured-challenges
│   ├── homemain
│   ├── partners
│   ├── rules
│   ├── testimonials
│   └── twitter-feed
├── nav
│   ├── footer
│   └── header-static
├── not-found
├── our-team
├── privacy-policy
├── profile
├── publiclists
│   ├── challengelist
│   │   └── challengecard
│   └── teamlist
│       └── teamcard
└── utility
    ├── cardlist
    ├── confirm
    ├── forcelogin
    ├── input
    ├── loading
    ├── modal
    ├── selectphase
    └── toast
```
Each leaf in this tree is a component. Each of this is a folder which contains these respective files _layout_ - `html`, _style_ - `scss`, _logic_ - `ts` and _test_ - `spec.ts`. 


#### Reusable Components
Usage example snippets for all of the following reusable components can be found in [Reusable Components Guide](https://github.com/Cloud-CV/EvalAI-ngx/blob/master/.github/REUSABLE_COMPONENTS.md).
- **Toast** — A custom notification component which displays success, error and info messages from the platform to the user.
- **Input** —Stylish form item component for making it easy to build forms and validations with support for input types: text, password, email and file.
- **Header** — Responsive Navigation Header with jump links.
- **Footer** — Responsive Navigation Footer with jump links.
- **Loading** — Loading gif overlay component (used in API calls wrapper right now)
- **Confirm** — Typescript callable Confirm modal for confirming from the user before making the operation (like delete operations)
- **Modal** — Typescript callable custom Modal with form items to be submitted (like update operations)
- **Forcelogin** — Used on pages with sections which should only be accessible to logged-in users. Users are redirected to the correct page when they log in.
- EvalAI Specific Reusable Components:
	- _Select Phase Component_ — This is a radio-card component in which only one phase can be selected at a time and a callback function is triggered whenever a phase is selected. (used on challenge-submit, submissions and leaderboard pages)
	- _Card List Component_ — This displays the list of challenges or teams (in the form of cards) based on the configuration. (used on challenges and teams pages)


### URL Structure

#### Static Pages 
These pages don't have variable / self-updating views.

Description | Path 
        --- | ---
Home Page (Landing Page) | `/`
About us Page | `/about`
Contact Us Page (with Map View) | `/contact`
Get-Involved Page | `/get-involved`
Our-team Page | `/our-team`
Privacy Policy Page (with smart-scrolling) | `/privacy-policy`
404 Not-Found page (🌩) | `/404`


#### Dynamic Pages
These pages contain variable / self-updating views.

Description | Path 
        --- | ---
Authentication Page (with support for: signUp, login, verify-email and email-verified) | `/auth/login` `/auth/signup` `/auth/verify-email/:token`
Profile Page (with support for: update-password, update-profile, fetching authentication-token) | `/profile`
Challenges List Page (list of public and hosted challenges with filters for upcoming, past and ongoing challenges) | `/challenges/all` `/challenges/me`
Teams Page (list of participant and host teams with options for creating new teams, editing teams, adding members to teams and deleting teams) | `/teams/participants` `/teams/hosts`
Dashboard Page (Links for ongoing challenges and teams) | `/dashboard`
Challenge Create Page (Zip Upload Page for Challenge-creation) | `/challenge-create`
Challenge Detail Page (Challenge details page with sub-pages for displaying overview, phase details, evaluation criteria, participate-in-challenge, make-submissions, view-submissions and displaying leaderboard) | `/challenge/<id>/overview` `/challenge/<id>/evaluation` `/challenge/<id>/phases` `/challenge/<id>/participate` `/challenge/<id>/submit` `/challenge/<id>/submissions` `/challenge/<id>/leaderboard`

### Creating new Components/Services
Use _Angular CLI's_ commands to generate new components or services.

> - `ng generate component components/<your-component>` to generate new components.
> - `ng generate service services/<your-service>` to generate new services.
