import { Injectable } from '@angular/core';

@Injectable()
export class EndpointsService {
  /**
   * Categories of API paths
   */
  participants = 'participants/';
  hosts = 'hosts/';
  jobs = 'jobs/';
  challenges = 'challenges/';
  challenge = 'challenge/';
  auth = 'auth/';
  analytics = 'analytics/';

  constructor() {}

  /**
   * Login URL
   */
  loginURL() {
    return `auth/login/`;
  }

  /**
   * Signup URL
   */
  signupURL() {
    return `auth/registration/`;
  }

  /**
   * Reset password URL
   */
  resetPasswordURL() {
    return `auth/password/reset/`;
  }

  /**
   * Reset password confirm URL
   */
  resetPasswordConfirmURL() {
    return `auth/password/reset/confirm`;
  }

  /**
   * Contact form URL
   */
  contactURL() {
    return `web/contact/`;
  }

  /**
   * Get User Details
   */
  userDetailsURL() {
    return `${this.auth}user/`;
  }

  /**
   * Change Password
   */
  changePasswordURL() {
    return `${this.auth}password/change/`;
  }

  /**
   * Verify Email
   */
  verifyEmailURL() {
    return `${this.auth}registration/verify-email/`;
  }

  featuredChallengesURL() {
    return `${this.challenges}featured/`;
  }

  /**
   * Subscribe to Newsletters
   */
  subscribeURL() {
    return `web/subscribe/`;
  }

  /**
   * All Participant teams
   */
  allParticipantTeamsURL() {
    return `${this.participants}participant_team`;
  }

  /**
   * Participant Teams Filter
   * @param teamName  team name
   */
  FilteredParticipantTeamURL(teamName) {
    return `${this.participants}participant_team?team_name=${teamName}`;
  }

  /**
   * Edit Participant Team Name
   */
  participantTeamURL(teamId) {
    return `${this.participants}participant_team/${teamId}`;
  }
  /**
   * Edit Host Team Name
   */
  hostTeamURL(teamId) {
    return `${this.hosts}challenge_host_team/${teamId}`;
  }

  /**
   * Host Teams Filter
   * @param teamName  team name
   */
  FilteredHostTeamURL(teamName) {
    return `${this.hosts}challenge_host_team?team_name=${teamName}`;
  }

  /**
   * Our Team members
   */
  ourTeamURL() {
    return `web/team/`;
  }

  /**
   * Invite members to participant team
   */
  participantTeamInviteURL(teamId) {
    return `${this.participants}participant_team/${teamId}/invite`;
  }

  /**
   * Fetch all challenges for a time frame
   * @param time  past, present or future
   */
  allChallengesURL(time) {
    return `${this.challenges}${this.challenge}${time}`;
  }

  /**
   * Fetch all unapproved challenges for a team
   * @param teamId  team Id
   */
  allUnapprovedChallengesURL(teamId) {
    return `${this.challenges}challenge_host_team/${teamId}/challenge`;
  }

  /**
   * All host teams
   */
  allHostTeamsURL() {
    return `${this.hosts}challenge_host_team`;
  }

  /**
   * Invite members to host team
   */
  hostTeamInviteURL(teamId) {
    return `${this.hosts}challenge_host_teams/${teamId}/invite`;
  }

  /**
   * Fetch challenge details for a given id
   * @param id  challenge id
   */
  challengeDetailsURL(id) {
    return `${this.challenges}${this.challenge}${id}/`;
  }

  /**
   * Challenge stars for a given challenge id
   * @param id  challenge id
   */
  challengeStarsURL(id) {
    return `${this.challenges}${id}/`;
  }

  /**
   * Challenge participant teams for a given challenge id
   * @param id  challenge id
   */
  challengeParticipantTeamsURL(id) {
    return `${this.participants}participant_teams/${this.challenges}${id}/user`;
  }

  /**
   * Challenge participate url for a given challenge id
   * @param id  challenge id
   * @param team  team id
   */
  challengeParticipateURL(id, team) {
    return `${this.challenges}${this.challenge}${id}/participant_team/${team}`;
  }

  /**
   * Challenge phase for a given challenge id
   * @param id  challenge id
   */
  challengePhaseURL(id) {
    return `${this.challenges}${this.challenge}${id}/challenge_phase`;
  }

  /**
   * Challenge phase details
   * @param id  challenge id
   * @param phaseId challenge phase id
   */
  updateChallengePhaseDetailsURL(id, phaseId) {
    return `${this.challenges}${this.challenge}${id}/challenge_phase/${phaseId}`;
  }

  /**
   * Challenge phase split for a given challenge id
   * @param id  challenge id
   */
  challengePhaseSplitURL(id) {
    return `${this.challenges}${id}/challenge_phase_split`;
  }

  /**
   * Challenge Creation
   * @param hostTeam  host team id
   */
  challengeCreateURL(hostTeam) {
    return `${this.challenges}${this.challenge}challenge_host_team/${hostTeam}/zip_upload/`;
  }

  /**
   * Challenge Leaderboard fetch
   * @param phaseSplitId  phase split id
   */
  challengeLeaderboardURL(phaseSplitId) {
    return `${this.jobs}challenge_phase_split/${phaseSplitId}/leaderboard/?page_size=1000`;
  }

  /**
   * Challenge Complete Leaderboard fetch for challenge host
   * @param phaseSplitId  phase split id
   */
  challengeCompleteLeaderboardURL(phaseSplitId) {
    return `${this.jobs}phase_split/${phaseSplitId}/public_leaderboard_all_entries/?page_size=1000`;
  }

  /**
   * Returns or Updates challenge phase split
   * @param phaseSplitId  phase split id
   */
  particularChallengePhaseSplitUrl(phaseSplitId) {
    return `${this.challenges}${this.challenge}create/challenge_phase_split/${phaseSplitId}/`;
  }

  /**
   * Challenge Submission
   * @param challenge  challenge id
   * @param phase  phase id
   */
  challengeSubmissionURL(challenge, phase) {
    return `${this.jobs}${this.challenge}${challenge}/challenge_phase/${phase}/submission/`;
  }

  /**
   * Filter challenge submissions in my submissions by participant team name
   * @param challenge challenge id
   * @param phase phase id
   * @param participantTeamName participant team name
   */
  challengeSubmissionWithFilterQueryURL(challenge, phase, participantTeamName) {
    return `${this.jobs}${this.challenge}${challenge}/challenge_phase/
${phase}/submission?participant_team__team_name=${participantTeamName}`;
  }

  /**
   * Get participated team name
   * @param challenge  challenge id
   */
  getParticipatedTeamNameURL(challenge) {
    return `${this.challenges}${challenge}/participant_team/team_detail`;
  }

  /**
   * Get all Challenge Submission
   * @param challenge  challenge id
   * @param phase  phase id
   */
  allChallengeSubmissionURL(challenge, phase) {
    return `${this.challenges}${challenge}/challenge_phase/${phase}/submissions`;
  }

  /**
   * Filter challenge submissions in view all submissions by participant team name
   * @param challenge challenge id
   * @param phase phase id
   * @param participantTeamName participant team name
   */
  allChallengeSubmissionWithFilterQueryUrl(challenge, phase, participantTeamName) {
    return `${this.challenges}${challenge}/challenge_phase/${phase}/submissions?participant_team__team_name=${participantTeamName}`;
  }

  /**
   * Challenge Submission Download
   * @param challenge  challenge id
   * @param phase  phase id
   */
  challengeSubmissionDownloadURL(challenge, phase, fileSelected) {
    return `${this.challenges}${challenge}/phase/${phase}/download_all_submissions/${fileSelected}/`;
  }

  /**
   * Challenge Submission Counts of the participant Team 
   * @param challenge  challenge id
   * @param phase  phase id
   */
  challengeSubmissionCountURL(challenge, phase) {
    return `${this.analytics}${this.challenge}${challenge}/challenge_phase/${phase}/count`;
  }

  /**
   * Challenge Submission Visibility
   * @param challenge  challenge id
   * @param phase  phase id
   * @param submission  submission id
   */
  challengeSubmissionUpdateURL(challenge, phase, submission) {
    return `${this.challengeSubmissionURL(challenge, phase)}${submission}`;
  }

  /**
   * Disable Challenge Submission
   * @param submission  submission id
   */
  disableChallengeSubmissionURL(submission) {
    return `${this.jobs}submission/${submission}`;
  }

  /**
   * Challenge Submissions Remaining
   * @param challenge  challenge id
   */
  challengeSubmissionsRemainingURL(challenge) {
    return `${this.jobs}${challenge}/remaining_submissions`;
  }

  /**
   * Edit challenge details
   * @param hostTeam challenge host team id
   * @param challenge challenge id
   */
  editChallengeDetailsURL(hostTeam, challenge) {
    return `${this.challenges}challenge_host_team/${hostTeam}/${this.challenge}${challenge}`;
  }

  getOrUpdateLeaderboardSchemaURL(leaderboard) {
    return `${this.challenges}${this.challenge}create/leaderboard/${leaderboard}/`;
  }

  /**
   * Delete challenge
   * @param challenge challenge id
   */
  deleteChallengeURL(challenge) {
    return `${this.challenges}${this.challenge}${challenge}/disable`;
  }

  /**
   * Re-run submission
   * @param submission submission id
   */
  reRunSubmissionURL(submission) {
    return `${this.jobs}submissions/${submission}/re-run-by-host/`;
  }

  /**
   * Team count analytics
   * @param challengeId challenge id
   */
  teamCountAnalyticsURL(challengeId) {
    return `${this.analytics}challenge/${challengeId}/team/count`;
  }

  /**
   * Challenge phase analytics
   * @param challengeId challenge id
   * @param phaseId phase id
   */
  challengePhaseAnalyticsURL(challengeId, phaseId) {
    return `${this.analytics}challenge/${challengeId}/challenge_phase/${phaseId}/analytics`;
  }

  /**
   * Challenge phase last submission analytics
   * @param challengeId challenge id
   * @param phaseId phase id
   */
  lastSubmissionAnalyticsURL(challengeId, phaseId) {
    return `${this.analytics}challenge/${challengeId}/challenge_phase/${phaseId}/last_submission_datetime_analysis/`;
  }

  /**
   * Challenge phase last submission analytics
   * @param challengeId challenge id
   * @param phaseId phase id
   */
  downloadParticipantsAnalyticsURL(challengeId) {
    return `${this.analytics}challenges/${challengeId}/download_all_participants/`;
  }

  /**
   * Manage worker
   * @param challengeId challenge id
   * @param action worker action
   */
  manageWorkerURL(challengeId, action) {
    return `${this.challenges}${challengeId}/manage_worker/${action}/`;
  }

  /**
   * Manage worker
   * @param challengeId challenge id
   */
  getLogsURL(challengeId) {
    return `${this.challenges}${challengeId}/get_worker_logs/`;
  }

  /**
   * Refresh auth token
   */
  refreshAuthTokenURL() {
    return `accounts/user/refresh_auth_token`;
  }

  /**
   * Get auth token
   */
  getAuthTokenURL() {
    return `accounts/user/get_auth_token`;
  }
}
