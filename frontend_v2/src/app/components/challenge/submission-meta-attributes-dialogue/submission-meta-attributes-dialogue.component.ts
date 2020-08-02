import { Component, OnInit, Optional, Inject  } from '@angular/core';
import { MatDialog, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';

@Component({
  selector: 'app-submission-meta-attributes-dialogue',
  templateUrl: './submission-meta-attributes-dialogue.component.html',
  styleUrls: ['./submission-meta-attributes-dialogue.component.scss']
})
export class SubmissionMetaAttributesDialogueComponent implements OnInit {
  /**
   * Meta attribute data
   */
  metaAttributesData: any;

  constructor(public dialog: MatDialog,
  public dialogRef: MatDialogRef<SubmissionMetaAttributesDialogueComponent>,
  @Optional() @Inject(MAT_DIALOG_DATA) public data: any) {
    this.metaAttributesData = data.attribute;
  }

  ngOnInit() {
  }

  closeDialog() {
    this.dialogRef.close({ event: 'close', data: this.metaAttributesData });
  }
}
