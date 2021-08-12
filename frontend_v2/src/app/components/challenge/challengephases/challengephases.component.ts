import { Component, OnInit } from '@angular/core';
import { ChallengeService } from '../../../services/challenge.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-challengephases',
  templateUrl: './challengephases.component.html',
  styleUrls: ['./challengephases.component.scss'],
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
   * @param challengeService  ChallengeService Injection.
   */
  constructor(private challengeService: ChallengeService) {}

  /**
   * Component on intialized
   */
  ngOnInit() {
    this.challengeService.currentChallenge.subscribe((challenge) => {
      this.challenge = challenge;
    });
    this.challengeService.currentPhases.subscribe((phases) => {
      this.phases = phases;
    });
  }
}
