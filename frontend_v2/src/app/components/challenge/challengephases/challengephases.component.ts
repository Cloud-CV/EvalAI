import { Component, OnInit, Inject } from '@angular/core';
import { DOCUMENT } from '@angular/common';
import { ChallengeService } from '../../../services/challenge.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-challengephases',
  templateUrl: './challengephases.component.html',
  styleUrls: ['./challengephases.component.scss']
})
export class ChallengephasesComponent implements OnInit {

  /**
   * Challenge object
   */
  challenge: any;

  /**
   * Challenge phases list
   */
  phases: any;

  /**
   * Constructor.
   * @param route  ActivatedRoute Injection.
   * @param router  GlobalService Injection.
   * @param authService  AuthService Injection.
   * @param globalService  GlobalService Injection.
   * @param apiService  Router Injection.
   * @param challengeService  ChallengeService Injection.
   */
  constructor(private challengeService: ChallengeService, @Inject(DOCUMENT) private document: Document) { }

  /**
   * Component on intialized
   */
  ngOnInit() {
    this.challengeService.currentChallenge.subscribe(
    challenge => {
      this.challenge = challenge;
    });
    this.challengeService.currentPhases.subscribe(
    phases => {
      this.phases = phases;
    });
  }
}
