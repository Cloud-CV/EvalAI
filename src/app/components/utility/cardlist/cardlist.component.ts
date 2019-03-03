import { Component, OnInit, Input } from '@angular/core';

/**
 * Component Class
 */
@Component({
  selector: 'app-cardlist',
  templateUrl: './cardlist.component.html',
  styleUrls: ['./cardlist.component.scss']
})
export class CardlistComponent implements OnInit {

  /**
   * Type of card (team/challenge)
   */
  @Input() type: string;

  /**
   * data object
   */
  @Input() data: object;

  /**
   * data observable
   */
  @Input() dataObservable: any;

  /**
   * delete team input event
   */
  @Input() deleteTeam: any;

  /**
   * Edit team input event
   */
  @Input() editTeam: any;

  /**
   * Add members to team input event
   */
  @Input() addMembersToTeam: any;

  /**
   * Select team input event
   */
  @Input() selectTeam: any;

  /**
   * list of elements
   */
  dataList: any;

  /**
   * Javascript Array object
   */
  arrayJavascript: any;

  /**
   * Constructor.
   */
  constructor() { }

  /**
   * Component on intialized.
   */
  ngOnInit() {
    this.arrayJavascript = Array;
    if (this.dataObservable) {
      this.dataObservable.subscribe((data) => {
        this.dataList = data;
      });
    }
  }

}
