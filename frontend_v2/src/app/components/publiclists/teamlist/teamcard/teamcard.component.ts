import { Component, OnInit, OnChanges, Input, Output, EventEmitter, SimpleChanges } from '@angular/core';
import { GlobalService } from '../../../../services/global.service';
import { ApiService } from '../../../../services/api.service';
import { Router, ActivatedRoute } from '@angular/router';
import { AuthService } from '../../../../services/auth.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-teamcard',
  templateUrl: './teamcard.component.html',
  styleUrls: ['./teamcard.component.scss']
})
export class TeamcardComponent implements OnInit, OnChanges {

  /**
   * Authentication Service subscription
   */
  authServiceSubscription: any;

  /**
   * Current Authentication state
   */
  authState: any;

  /**
   * Team object
   */
  @Input() team: object;

  /**
   * Selected flag
   */
  @Input() selected: boolean;

  /**
   * Update
   */
  @Input() isOnChallengePage: boolean;

  /**
   * Delete team event
   */
  @Output() deleteTeamCard = new EventEmitter<any>();

  /**
   * Delete member event
   */
  @Output() deleteMemberCard = new EventEmitter<any>();

  /**
   * Select team event
   */
  @Output() selectTeamCard = new EventEmitter<any>();

  /**
   * Deselect team event
   */
  @Output() deselectTeamCard = new EventEmitter<any>();

  /**
   * Edit team event
   */
  @Output() editTeamCard = new EventEmitter<any>();

  /**
   * Add members event
   */
  @Output() addMembersTeamCard = new EventEmitter<any>();

  /**
   * Team relatd text
   */
  teamText = '';

  /**
   * Team view object
   */
  teamView = {};

  /**
   * Team Member Array
   */
  memberArray = [];

  /**
   * Team Member ID Array
   */
  memberIdArray = [];

  /**
   * Is currently selected
   */
  isSelected = false;

  /**
   * Is a host team
   */
  isHost = false;

  /**
   * Constructor.
   * @param route  ActivatedRoute Injection.
   * @param router  Router Injection.
   * @param globalService  GlobalService Injection.
   * @param apiService  ApiService Injection.
   */
  constructor(private globalService: GlobalService,
              private apiService: ApiService,
              public authService: AuthService,
              private router: Router,
              private route: ActivatedRoute) { }

  /**
   * Component on initialized.
   */
  ngOnInit() {
    this.updateView();
    this.authServiceSubscription = this.authService.change.subscribe((authState) => {
      this.authState = authState;
    });
  }

  /**
   * Component on change detected.
   * @param changes  changes detected in the inputs.
   */
  ngOnChanges(changes: SimpleChanges) {
    this.updateView();
  }

  /**
   * Select a team content toggle.
   */
  selectTeamContentToggle() {
    this.isSelected = !this.isSelected;
    this.team['isSelected'] = this.isSelected;
    this.deselectTeamCard.emit(this.team);
  }

  /**
   * Select a team toggle.
   */
  selectTeamToggle() {
    if (this.isHost || this.isOnChallengePage) {
      this.isSelected = !this.isSelected;
      this.selectTeam();
    }
  }

  /**
   * Fires team edit event.
   */
  editTeam(e) {
    e.stopPropagation();
    this.editTeamCard.emit(this.team);
  }

  /**
   * Fires add members to team event.
   */
  addMembersToTeam(e) {
    e.stopPropagation();
    this.addMembersTeamCard.emit(this.team['id']);
  }

  /**
   * Fires delete team event.
   */
  deleteTeam(e) {
    e.stopPropagation();
    this.deleteTeamCard.emit(this.team['id']);
  }

    /**
   * Fires delete member event.
   */
  deleteTeamMember(e, participantId) {
    e.stopPropagation();
    this.deleteMemberCard.emit({teamId: this.team['id'], participantId: participantId});
  }

  /**
   * Fires slect team event.
   */
  selectTeam() {
    this.selectTeamCard.emit(this.team);
  }

  /**
   * UI view update, called after onInit.
   */
  updateView() {
    this.teamView['team_name'] = this.team['team_name'];
    this.teamView['created_by'] = this.team['created_by'];
    this.teamView['team_url'] = this.team['team_url'];
    if (this.team['isHost']) {
      this.isHost = true;
    }
    if (this.team['isSelected']) {
      this.isSelected = true;
    } else {
      this.isSelected = false;
    }
    const temp = this.team['members'];
    this.memberArray = [];
    this.memberIdArray = [];
    for (let i = 0; i < temp.length; i++) {
      if (temp[i]['member_name']) {
        this.memberArray.push(temp[i]['member_name']);
        this.memberIdArray.push(temp[i]['id']);
      } else {
        this.memberArray.push(temp[i]['user']);
        this.memberIdArray.push(temp[i]['id']);
      }
    }
    this.teamView['members'] = this.memberArray;
    this.teamView['member_ids'] = this.memberIdArray;
  }

}
