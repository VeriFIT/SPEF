#include <iostream>
#include <string.h>
#include <ncurses.h>
#include <algorithm>
#include <ctype.h>
#include "hangman.h"


using namespace std;

/* prints stats about all tries during game, wrong guesses and used letters */
void print_stats(WINDOW *win, int row, int col, int tries, int wrong, int max, char *used){
    string tries_mess = "Tries: " + to_string(tries);
    string wrong_mess = "Wrong: " + to_string(wrong) + "/" + to_string(max);
    string used_mess = "Used: ";
    for(int i=0;i<tries;i++){
        if(i==0)
            used_mess = used_mess + used[i];
        else
            used_mess = used_mess + ", " + used[i];
    }
    print_at_line(win, 1, false, col, tries_mess.c_str());
    print_at_line(win, 2, false, col, wrong_mess.c_str());
    print_at_line(win, 3, false, col, used_mess.c_str());
}

/* prints message with game status (win/lose) and shows full guessed message from game 
then waits for user input to exit game */
void game_over_message(WINDOW *win, bool lose, int row, int col, char *mess){
    clear_win(win);
    print_at_line(win, 1, true, col, "***** GAME OVER *****");
    if(lose){
        print_at_line(win, 3, true, col, "You lost. The message was: ");
    } else{
        print_at_line(win, 3, true, col, "You won ! Congrats :)");
    }
    static_cast<void>(guess_message(win, row, col, mess, NULL, true)); // static_cast bcs we know that we dont need return value and its safe
    print_at_line(win, 9, true, col, "Press any key to exit");
    wgetch(win);
}

/* function for printing message in the center or some lines up/down from center */
void print_at_line(WINDOW *win, int line, bool center, int col, const char *message){
    if(center)
        mvwprintw(win, line, (col-strlen(message))/2, message);
    else
        mvwprintw(win, line, 5, message);
    wrefresh(win);
}


void print_hangman(WINDOW *win, int number, int col){
    int center = (col-strlen("__|_______"))/2;
    switch(number)
    {
    case 0:
        mvwprintw(win, 1, center, "  |====|  ");
        mvwprintw(win, 2, center, "  |       ");
        mvwprintw(win, 3, center, "  |       ");
        mvwprintw(win, 4, center, "  |       ");
        mvwprintw(win, 5, center, "__|_______");
        wrefresh(win);
        break;
    case 1:
        mvwprintw(win, 1, center, "  |====|  ");
        mvwprintw(win, 2, center, "  |    O  ");
        mvwprintw(win, 3, center, "  |       ");
        mvwprintw(win, 4, center, "  |       ");
        mvwprintw(win, 5, center, "__|_______");
        wrefresh(win);
        break;
    case 2:
        mvwprintw(win, 1, center, "  |====|  ");
        mvwprintw(win, 2, center, "  |    O  ");
        mvwprintw(win, 3, center, "  |    |  ");
        mvwprintw(win, 4, center, "  |       ");
        mvwprintw(win, 5, center, "__|_______");
        wrefresh(win);
        break;
    case 3:
        mvwprintw(win, 1, center, "  |====|  ");
        mvwprintw(win, 2, center, "  |    O  ");
        mvwprintw(win, 3, center, "  |   /|  ");
        mvwprintw(win, 4, center, "  |       ");
        mvwprintw(win, 5, center, "__|_______");
        wrefresh(win);
        break;
    case 4:
        mvwprintw(win, 1, center, "  |====|  ");
        mvwprintw(win, 2, center, "  |    O  ");
        mvwprintw(win, 3, center, "  |   /|\\");
        mvwprintw(win, 4, center, "  |       ");
        mvwprintw(win, 5, center, "__|_______");
        wrefresh(win);
        break;
    case 5:
        mvwprintw(win, 1, center, "  |====|  ");
        mvwprintw(win, 2, center, "  |    O  ");
        mvwprintw(win, 3, center, "  |   /|\\");
        mvwprintw(win, 4, center, "  |   /   ");
        mvwprintw(win, 5, center, "__|_______");
        wrefresh(win);
        break;
    case 6:
        mvwprintw(win, 1, center, "  |====|  ");
        mvwprintw(win, 2, center, "  |    O  ");
        mvwprintw(win, 3, center, "  |   /|\\");
        mvwprintw(win, 4, center, "  |   / \\");
        mvwprintw(win, 5, center, "__|_______");
        wrefresh(win);
        break;
    default:
        break;
    };

}

/* prints guessed message (in the center of the window) with empty underline for unknown letters 
or prints full message in case variable "show_all" is true */
bool guess_message(WINDOW *win, int row, int col, char *mess, char *used, bool show_all){
    bool game_over = true;
    wmove(win, row/2, (col-(strlen(mess)*2))/2); // move to the center
    for(char *i = mess; *i; ++i){
        char c = toupper(*i);
        if(c == ' '){
            waddch(win,' '); // space between words in message
        } else if(show_all || memchr(used, c, strlen(used))){
            waddch(win,c | A_UNDERLINE);
        } else{
            waddch(win,' ' | A_UNDERLINE); // letter wasnt quessed yet
            game_over = false;
        }
        waddch(win,' '); // space between letters
    }
    wrefresh(win);
    return game_over;
}

WINDOW *create_win(int width, int height, int start_x, int start_y){
    WINDOW *new_win = newwin(height,width,start_y,start_x);
    box(new_win,0,0);
    wrefresh(new_win);
    return new_win;
}

void clear_win(WINDOW *win){
    wclear(win);
    box(win,0,0);
    wrefresh(win);
}

void destroy_win(WINDOW *win){
    wclear(win);
    wborder(win,' ',' ',' ',' ',' ',' ',' ',' ');
    wrefresh(win);
    delwin(win);
}

/* check if input message includes alphabet only and its not empty
0 ok
1 non-aplha
2 empty
3 only whitespace
*/
int process_input(char *mess){
    bool includes_letter = false;
    int mess_len = strlen(mess);
    if(mess_len==0)
        return 2;
    for(int i=0;i<mess_len;i++){
        if(!isalpha(mess[i]) && !isspace(mess[i]))
            return 1;
        else{
            mess[i] = toupper(mess[i]);
            if(isalpha(mess[i]))
                includes_letter = true;
        }
    }
    if(!includes_letter)
        return 3;
    return 0;
}

void play_hangman(){
    /* init game */
    int row, col, global_row, global_col, man_win_row, man_win_col;
    getmaxyx(stdscr,global_row,global_col);
    char used[25]; // used letters
    int tries=0; // number of total tries
    int max_guess=6; // number of max wrong guesses
    int wrong_guess=0; // wrong guesses
    char input_mess[100]; // message to quess
    memset(input_mess,0,100);
    memset(used,0,25);
    char input_c;
    bool game_over = false;
    bool lose = false;

    /* print welcome message */
    string welcome_mess = "H A N G M A N"; 
    mvprintw(1,(global_col-welcome_mess.size())/2,welcome_mess.c_str());
    refresh();

    /* prepare window for guessing */
    int word_win_width = 60;
    int word_win_height = 12;
    int word_win_x = (global_col-word_win_width)/2;
    int word_win_y = 2;
    WINDOW *word_win = create_win(word_win_width,word_win_height,word_win_x,word_win_y);
    getmaxyx(word_win,row,col);

    /* prepare window for hangman */
    int man_win_width = 30;
    int man_win_height = 7;
    int man_win_x = (global_col-man_win_width)/2;
    int man_win_y = word_win_y+word_win_height;
    WINDOW *man_win = create_win(man_win_width,man_win_height,man_win_x,man_win_y);
    getmaxyx(man_win,man_win_row,man_win_col);


    /* get input message to guess */
    print_at_line(word_win, 2, true, col, "Please enter your message");
    print_at_line(word_win, 3, true, col, "(use only alphabet symbols)");
    print_at_line(word_win, 6, true, col, " "); // move cursor to line 6
    wgetnstr(word_win, input_mess, 99); // get input string (max 99s char long)
    int ret_num = process_input(input_mess); // check input and make it uppercase
    while(ret_num!=0){
        if(ret_num == 1){
            clear_win(word_win);
            print_at_line(word_win, 2, true, col, "You used some non-alphabet symbol!");
            print_at_line(word_win, 3, true, col, "Try enter your message again");
            print_at_line(word_win, 4, true, col, "or just press enter to exit");
            print_at_line(word_win, 5, true, col, "(use only alphabet symbols)");
            print_at_line(word_win, 6, true, col, " "); // move cursor to line 6
        }else if(ret_num == 2){
            clear_win(word_win);
            print_at_line(word_win, 4, true, col, "You ended the game by entering an empty message");
            print_at_line(word_win, 9, true, col, "Press any key to exit");
            wgetch(word_win);
            destroy_win(word_win);
            destroy_win(man_win);
            return; // exit game
        }else if(ret_num == 3){
            clear_win(word_win);
            print_at_line(word_win, 2, true, col, "Your message doesnt include any letters!");
            print_at_line(word_win, 3, true, col, "Try enter your message again");
            print_at_line(word_win, 4, true, col, "or just press enter to exit");
            print_at_line(word_win, 5, true, col, "(use only alphabet symbols)");
            print_at_line(word_win, 6, true, col, " "); // move cursor to line 6
        }
        wgetnstr(word_win, input_mess, 99);
        ret_num = process_input(input_mess);
    }

    /* print empty guessing word */
    clear_win(word_win);
    print_stats(word_win, row, col, tries, wrong_guess, max_guess, used);
    static_cast<void>(guess_message(word_win, row, col, input_mess, used, false)); // static_cast bcs so we know that we dont need return value of function guess_message
    print_hangman(man_win,wrong_guess,man_win_col);

    /* start quessing */
    while(!game_over){
        char input_c = toupper(wgetch(word_win)); // get char from user input
        if(!isalpha(input_c))
            continue;

        if(!memchr(used, input_c, strlen(used))){
            used[tries++] = input_c; // add user input into used letters
            if(!memchr(input_mess, input_c, strlen(input_mess)))
                wrong_guess++; // increment wrong quess
        }
        print_stats(word_win, row, col, tries, wrong_guess, max_guess, used);
        game_over = guess_message(word_win, row, col, input_mess, used, false);
        print_hangman(man_win,wrong_guess,man_win_col);

        if(wrong_guess==max_guess){
            game_over = true;
            lose = true;
        }
    }
    game_over_message(word_win,lose,row,col,input_mess);
    destroy_win(word_win);
    destroy_win(man_win);
}



int main(int argc, char ** argv){

    initscr(); // init screen for ncurses, clears the screen and presents a blank screen and allocates memory

    // raw(); // ctrl+c dont kill the program
    keypad(stdscr, TRUE); // accept Fx keys and arrows
    noecho(); // dont print pressed key while getch (and doesnt update xy coordinates with print)

    play_hangman();

    endwin(); // free memory and ends ncurses
    return 0;
}

