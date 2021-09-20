import { Component, OnInit, Input, OnChanges } from '@angular/core';
import { ChallengeService } from '../../../services/challenge.service';
import { GlobalService } from '../../../services/global.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-selectphase',
  templateUrl: './selectphase.component.html',
  styleUrls: ['./selectphase.component.scss'],
})
export class SelectphaseComponent implements OnInit, OnChanges {
  /**
   * Phase list
   */
  @Input() phases: any;

  /**
   * Phase Splits list for settings tab
   */
  @Input() settingsPhaseSplits: any;

  /**
   * Phase Splits list
   */
  @Input() phaseSplits: any;

  /**
   * Selected phase callback
   */
  @Input() phaseSelected: any;

  /**
   * Selected phase split callback to update the router URL
   */
  @Input() selectedPhaseSplitUrlChange: any;

  /**
   * Selected phase split
   */
  @Input() phaseSplitSelected: any;

  /**
   * Phase selection type (radio button or select box)
   */
  @Input() phaseSelectionType: string;

  /**
   * Phase selection list type (phase or phase split)
   */
  @Input() phaseSelectionListType: string;

  /**
   * Selected phase name
   */
  phaseName = '';

  /**
   * Selected phase visibility
   */
  phaseVisibility = false;

  /**
   * If phase selected
   */
  isPhaseSelected = false;

  /**
   * Currently selected phase
   */
  selectedPhase: any = null;

  /**
   * Selected split name
   */
  splitName = '';

  /**
   * Selected split name
   */
  settingsSplitName = '';

  /**
   * Selected phase split
   */
  selectedPhaseSplit = '';

  /**
   * If phase selected
   */
  isPhaseSplitSelected = false;

  /**
   * Challenge object
   */
  challenge: any;

  /**
   * Select default radio option if same as phase id
   */
  radioSelected: number;

  /**
   * Constructor.
   * @param globalService  GlobalService Injection.
   * @param challengeService  ChallengeService Injection.
   */
  constructor(private challengeService: ChallengeService, private globalService: GlobalService) {}

  /**
   * Component on intialized.
   */
  ngOnInit() {
    this.challengeService.currentChallenge.subscribe((challenge) => {
      this.challenge = challenge;
    });

    if (Array.isArray(this.phases) && this.phases.length) {
      this.selectedPhase = this.phases[0];
      this.radioSelected = this.phases[0].id;
      this.selectPhase(this.phases[0]);
    } else if (Array.isArray(this.settingsPhaseSplits) && this.settingsPhaseSplits.length) {
      this.selectedPhaseSplit = this.settingsPhaseSplits[0];
      this.selectSettingsPhaseSplit(this.settingsPhaseSplits[0], 'selectBox', 'settingsPhaseSplit');
    } else if (Array.isArray(this.phaseSplits) && this.phaseSplits.length) {
      this.selectedPhaseSplit = this.phaseSplits[0];
      this.selectPhaseSplit(this.phaseSplits[0], 'selectBox', 'phaseSplit');
    }
  }

  /**
   * Component on changes detected in Input.
   * @param change  changes detected
   */
  ngOnChanges(change) {
    this.challengeService.isPhaseSelected.subscribe((isPhaseSelected) => {
      this.isPhaseSelected = isPhaseSelected;
    });

    if (this.isPhaseSelected === true && this.phaseSelected) {
      this.challengeService.changePhaseSelected(false);
      this.selectPhase(this.selectedPhase);
    }

    this.challengeService.isPhaseSplitSelected.subscribe((isPhaseSplitSelected) => {
      this.isPhaseSplitSelected = isPhaseSplitSelected;
    });

    if (this.phaseSplitSelected && this.isPhaseSplitSelected) {
      this.challengeService.changePhaseSplitSelected(false);
      this.selectSettingsPhaseSplit(this.selectedPhaseSplit, this.phaseSelectionType, this.phaseSelectionListType);
    }
  }

  /**
   * Select a particular phase.
   * @param phase  phase to be selected.
   */
  selectPhase(phase) {
    this.selectedPhase = phase;
    this.phaseName = phase.name;
    this.phaseVisibility = phase.showPrivate;
    this.phaseSelected(phase);
  }

  /**
   * Select a particular phase split.
   * @param phaseSplit  phase split to be selected.
   * @param phaseSelectionType phase selection type (radio button or select box).
   * @param phaseSelectionListType phase selection list type (phase or phase split)
   */

  selectSettingsPhaseSplit(phaseSplit, phaseSelectionType, phaseSelectionListType) {
    this.phaseSelectionType = phaseSelectionType;
    this.phaseSelectionListType = phaseSelectionListType;
    this.selectedPhaseSplit = phaseSplit;
    this.phaseName = phaseSplit.challenge_phase_name;
    this.settingsSplitName = phaseSplit.dataset_split_name;
    this.phaseVisibility = phaseSplit.showPrivate;
    this.phaseSplitSelected(phaseSplit);
  }

  selectPhaseSplit(phaseSplit, phaseSelectionType, phaseSelectionListType) {
    this.phaseSelectionType = phaseSelectionType;
    this.phaseSelectionListType = phaseSelectionListType;
    this.selectedPhaseSplit = phaseSplit;
    this.phaseName = phaseSplit.challenge_phase_name;
    this.splitName = phaseSplit.dataset_split_name;
    this.phaseVisibility = phaseSplit.showPrivate;
    this.selectedPhaseSplitUrlChange(phaseSplit);
  }

  /**
   * Get 12Hour formatted date function.
   */
  getFormattedDate(date) {
    return this.globalService.formatDate12Hour(new Date(Date.parse(date)));
  }
}
