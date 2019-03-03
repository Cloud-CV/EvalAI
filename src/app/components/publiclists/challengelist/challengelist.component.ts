import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../../services/api.service';
import { GlobalService } from '../../../services/global.service';
import { AuthService } from '../../../services/auth.service';
import { Router, ActivatedRoute } from '@angular/router';

/**
 * Component Class
 */
@Component({
  selector: 'app-challengelist',
  templateUrl: './challengelist.component.html',
  styleUrls: ['./challengelist.component.scss']
})
export class ChallengelistComponent implements OnInit {

  /**
   * Filter toggle flag
   */
  isUpcomingChecked = true;

  /**
   * Filter toggle flag
   */
  isOngoingChecked = true;

  /**
   * Filter toggle flag
   */
  isPastChecked = false;

  /**
   * Upcoming challenges list
   */
  upcomingChallenges = [];

  /**
   * Ongoing challenges list
   */
  ongoingChallenges = [];

  /**
   * Past challeges list
   */
  pastChallenges = [];

  /**
   * API common path
   */
  apiPathCommon = 'challenges/challenge/';

  /**
   * API path mapping
   */
  apiPathMapping = {
    isUpcomingChecked: this.apiPathCommon + 'future',
    isOngoingChecked: this.apiPathCommon + 'present',
    isPastChecked: this.apiPathCommon + 'past'
  };

  /**
   * List of filtered challenges
   */
  filteredChallenges = [];

  /**
   * List of filtered-further challenges
   */
  filteredChallengesView = [];

  /**
   * Team list
   */
  allTeams = [];

  /**
   * Display more frames of teams
   */
  seeMore = 1;

  /**
   * Frame size
   */
  windowSize = 10;

  /**
   * Auth service public instance
   */
  authServicePublic: AuthService;

  /**
   * Router public instance
   */
  routerPublic: Router;

  /**
   * Is user Logged in
   */
  isLoggedIn: any = false;

  /**
   * Constructor.
   * @param route  ActivatedRoute Injection.
   * @param router  Router Injection.
   * @param globalService  GlobalService Injection.
   * @param authService  AuthService Injection.
   * @param apiService  ApiService Injection.
   */
  constructor(private apiService: ApiService,
              private authService: AuthService,
              private globalService: GlobalService,
              private router: Router,
              private route: ActivatedRoute) { }

  /**
   * Component on intialized.
   */
  ngOnInit() {
    if (this.authService.isLoggedIn()) {
      this.isLoggedIn = true;
    }
    if (this.router.url === '/challenges/all') {
      this.fetchChallenges();
    } else if (this.router.url === '/challenges/me' && this.authService.isLoggedIn()) {
      this.fetchMyTeams();
    }
    this.authServicePublic = this.authService;
    this.routerPublic = this.router;
  }

  /**
   * Fetch teams function.
   */
  fetchMyTeams() {
    // this.fetchTeams('participants/participant_team');
    this.fetchTeams('hosts/challenge_host_team');
  }

  /**
   * Toggle upcoming/past/ongoing filters.
   * @param filter  selected filter
   */
  toggleFilter(filter) {
    this[filter] = !this[filter];
    if (this[filter]) {
      this.fetchChallenges(filter);
    } else {
      this.upcomingChallenges = filter === 'isUpcomingChecked' ? [] : this.upcomingChallenges;
      this.ongoingChallenges = filter === 'isOngoingChecked' ? [] : this.ongoingChallenges;
      this.pastChallenges = filter === 'isPastChecked' ? [] : this.pastChallenges;
      this.filteredChallenges = this.upcomingChallenges.concat(this.ongoingChallenges, this.pastChallenges);
      this.updateChallengesView(true);
    }
  }

  /**
   * Show more results.
   */
  seeMoreClicked() {
    this.seeMore = this.seeMore + 1;
    this.updateChallengesView(false);
  }

  /**
   * Update challenges view (called after fetching challenges from API).
   * @param reset  reset flag for hiding/showing more results
   */
  updateChallengesView(reset) {
    if (reset) {
      this.seeMore = 1;
    }
    this.filterChallengesByTeams();
    this.filteredChallengesView = this.filteredChallenges.slice(0, (this.seeMore * this.windowSize));
  }

  /**
   * Filtering challenges by teams
   */
  filterChallengesByTeams() {
    if (this.router.url === '/challenges/me' && this.authService.isLoggedIn()) {
      this.filteredChallenges = this.filteredChallenges.filter((v, i, a) => this.allTeams.indexOf(v['creator']['id']) > -1);
    }
  }

  /**
   * Fetch teams function.
   * @param path  teams fetch URL
   */
  fetchTeams(path) {
    const SELF = this;
    SELF.filteredChallenges = [];
    this.apiService.getUrl(path).subscribe(
      data => {
        if (data['results']) {
          const TEAMS = data['results'].map((item) => item['id']);
          SELF.allTeams = SELF.allTeams.concat(TEAMS);
          SELF.allTeams = SELF.allTeams.filter((v, i, a) => a.indexOf(v) === i);
          SELF.fetchChallenges();
        }
      },
      err => {
        SELF.globalService.handleApiError(err, false);
      },
      () => {
        console.log('Teams fetched', path);
      }
    );
  }

  /**
   * Fetch Challenges function.
   * @param filter  selected filter
   * @param callback  callback function
   */
  fetchChallenges(filter = null, callback = null) {
    if (!filter) {
      const ALL_PATHS = Object.values(this.apiPathMapping);
      const ALL_KEYS = Object.keys(this.apiPathMapping);
      for (let i = 0; i < ALL_PATHS.length; i++) {
        if (this[ALL_KEYS[i]]) {
          this.fetchChallengesFromApi(ALL_PATHS[i], callback);
        }
      }
    } else {
      this.fetchChallengesFromApi(this.apiPathMapping[filter], callback);
    }
  }

  /**
   * Fetch challenges from backend.
   * @param path  Challenge fetch URL
   * @param callback  Callback Function.
   */
  fetchChallengesFromApi(path, callback = null) {
    const SELF = this;
    SELF.apiService.getUrl(path).subscribe(
      data => {
        if (path.endsWith('future')) {
          SELF.upcomingChallenges = data['results'];
        } else if (path.endsWith('present')) {
          SELF.ongoingChallenges = data['results'];
        } else if (path.endsWith('past')) {
          SELF.pastChallenges = data['results'];
        }
        SELF.filteredChallenges = SELF.upcomingChallenges.concat(SELF.ongoingChallenges, SELF.pastChallenges);
        this.updateChallengesView(true);
      },
      err => {
        SELF.globalService.handleApiError(err);
      },
      () => console.log(path.slice(SELF.apiPathCommon.length) + ' challenges fetched!')
    );
  }

}
