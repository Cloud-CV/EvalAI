import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { CardlistComponent } from './cardlist.component';
import { ChallengecardComponent } from '../../publiclists/challengelist/challengecard/challengecard.component';
import { TeamcardComponent } from '../../publiclists/teamlist/teamcard/teamcard.component';

describe('CardlistComponent', () => {
  let component: CardlistComponent;
  let fixture: ComponentFixture<CardlistComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ CardlistComponent, ChallengecardComponent, TeamcardComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CardlistComponent);
    component = fixture.componentInstance;
    component.type = 'challenges';
    component.data = [];
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
