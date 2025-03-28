import { Component, OnInit } from '@angular/core';

// import service
import { ChallengeService } from '../../../services/challenge.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-challengeoverview',
  templateUrl: './challengeoverview.component.html',
  styleUrls: ['./challengeoverview.component.scss'],
})
export class ChallengeoverviewComponent implements OnInit {
  /**
   * Challenge object
   */
  challenge: any = null;

  /**
   * Is challenge host
   */
  isChallengeHost = false;

  /**
   * Constructor.
   * @param challengeService  ChallengeService Injection.
   */
  constructor(private challengeService: ChallengeService) {}

  /**
   * Component on initialized.
   */
  ngOnInit() {
    this.challengeService.currentChallenge.subscribe((challenge) => {
      this.challenge = challenge;
    });
    this.challengeService.isChallengeHost.subscribe((status) => {
      this.isChallengeHost = status;
    });
  }
}
